
# app/services/v2/recommender.py
# 역할:
# - 추천 점수 계산과 랭킹을 담당하는 서비스 레이어
# - 본 뼈대는 "clustering 모델"을 적용합니다.
# fallback
# 1. - model 하루에 한 번 다시 돌리는 경우 -> v1의 로직 사용
# 2. - model 먹통 -> v1의 로직 사용
# 3. - 비로그인 유저 -> 일반 콜드스타트
# - 콜드스타트가 아닌 이상 시간/인기(popularity) 신호는 사용하지 않습니다.

# 가정: 사용자 선호 카테고리는 최대 3개, 방의 카테고리는 정확히 1개입니다.

# 의존: models/schemas.py(DTO), (선택) processors/preprocessors.py(카테고리 정규화)

# 언제 호출되는가:
# - 엔드포인트(app/api/v1/endpoints/recommendations.py)에서
#   HTTP 요청을 검증한 뒤, 이 서비스의 rank() 메서드를 호출합니다.
#   내부 로직 변경 시, app/services/v1/recommender.py 여기서만 작업할 것 recommendations 변경 X
# app/services/recommender.py

from __future__ import annotations
from pathlib import Path
import joblib
import json
import numpy as np

from typing import List, Dict, Iterable, Optional
from datetime import datetime, timezone

from app.core.config import settings

from app.models.domain import RoomRecommandUserMetaV2

from app.models.enums import Category


class Recommender:
    def __init__(self, artifacts_dir: Path | None = None):
        """
        app/cluster/gatherings_popularity.py
        app/cluster/user_clustering.py
        그 전에 생성된 모델을 불러와 단순하게 해당 cluster에 대한 추천만 해주면 되는거다.

        """
        if artifacts_dir is None:
            artifacts_dir = Path(settings.CLUSTER_ARTIFACT_DIR)
        else:
            artifacts_dir = Path(artifacts_dir)

        self.artifacts_dir: Path = artifacts_dir

        self.artifacts_loaded = False  # 기본값
        try:
            self.scaler = joblib.load(self.artifacts_dir / "scaler.pkl")
            self.svd = joblib.load(self.artifacts_dir / "svd.pkl")
            self.kmeans = joblib.load(self.artifacts_dir / "kmeans.pkl")

            with open(artifacts_dir / "category_vocab.json", "r", encoding="utf-8") as f:
                self.category_vocab = json.load(f)

            # {category: index}
            self.cat_index = {c: i for i, c in enumerate(self.category_vocab)}

            # 2) popularity 아티팩트 로드 -> rank에서 바로 써먹음.
            #    popularity 디렉토리는 user_clustering 디렉토리의 형제 디렉토리로 가정:
            #    app/clusters/artifacts/user_clustering
            #    app/clusters/artifacts/popularity
            popularity_dir = Path(settings.POPULARITY_ARTIFACT_DIR)
            self.popularity_path = popularity_dir / "cluster_popularity.json"

            if self.popularity_path.exists():
                with self.popularity_path.open("r", encoding="utf-8") as f:
                    self.cluster_popularity: Dict[str, List[int]] = json.load(f)
            else:
                # 아직 popularity 배치가 안 돌았을 수도 있으므로 빈 dict로 시작
                self.cluster_popularity = {}

            self.artifacts_loaded = True
            print("[Recommender v2] artifacts loaded.")

        except FileNotFoundError:
            # 아티팩트 아직 없음 → 항상 v1 fallback
            print("[Recommender v2] artifacts not found. Will fallback to v1.")
            self.category_vocab = []
            self.cat_index = {}
            self.cluster_popularity = {}

    # -------------------------------
    # public API : cluster_id 유뮤에 상관없음,
    # -> predict를 해서 다시 실행을 하든, 원래 있든 기존에 있던 아티팩트에서 추천방을 뺴오기만 하면 된다.
    # -------------------------------
    def rank(
            self,
            user=RoomRecommandUserMetaV2,
            limit: int = settings.RECOMMANDS_LIMIT,
            now: Optional[datetime] = None,
    ) -> Optional[List[int]]:

        if not getattr(self, "artifacts_loaded", False):
            # fallback 정책(1)
            # 아티팩트 자체가 아직 없으면 무조건 v1로 넘김
            return None

        if user.user_id is None or not self.cluster_popularity:
            # fallback 정책(2)
            # - 비로그인 유저 (user_id 없음)
            # - popularity 아티팩트 없음/비어 있음
            return None

        cluster_id = self.predict_cluster(user)

        # 2. cluster별 인기방 목록 조회
        key = str(cluster_id)
        room_ids_for_cluster = self.cluster_popularity.get(key, [])

        if not room_ids_for_cluster:
            # TODO: 여기서 v1 콜드스타트/글로벌 인기방 fallback 넣을 수 있음
            return []

        # 3. 상위 limit 개만 잘라서 반환
        return room_ids_for_cluster[:limit]

    # -------------------------------
    # public API : cluster 예측, RecommendByClusteringModelRequest cluster_id 없을 경우
    # -------------------------------

    def predict_cluster(self, req: RoomRecommandUserMetaV2) -> int:
        # 1. numeric feature
        age = req.user_age or 0
        enroll = req.user_enroll or 0
        join = req.user_join_count or 0
        numeric = np.array([[age, enroll, join]], dtype=np.float32)

        # 2. multi-hot
        multi = np.zeros((1, len(self.category_vocab)), dtype=np.float32)
        for cat in (req.preferred_categories or []):
            name = Category._cat_name(cat)   # Enum -> "음악" 같은 문자열
            idx = self.cat_index.get(name)
            if idx is not None:
                multi[0, idx] = 1.0

        # 3. SVD transform
        svd_vec = self.svd.transform(multi)

        # 4. concat numeric + svd
        X = np.hstack([numeric, svd_vec])

        # 5. scaling
        X_scaled = self.scaler.transform(X)

        # 6. cluster 예측
        cluster_id = int(self.kmeans.predict(X_scaled)[0])

        return cluster_id
