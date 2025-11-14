
# app/services/v1/recommender.py
# 역할:
# - 추천 점수 계산과 랭킹을 담당하는 서비스 레이어
# - 본 뼈대는 "카테고리 유사도 B안(확률 내적 + 스케일)"을 적용합니다.
# - 콜드스타트가 아닌 이상 시간/인기(popularity) 신호는 사용하지 않습니다.

# 가정: 사용자 선호 카테고리는 최대 3개, 방의 카테고리는 정확히 1개입니다.

# 의존: models/schemas.py(DTO), (선택) processors/preprocessors.py(카테고리 정규화)

# 언제 호출되는가:
# - 엔드포인트(app/api/v1/endpoints/recommendations.py)에서
#   HTTP 요청을 검증한 뒤, 이 서비스의 rank() 메서드를 호출합니다.
#   내부 로직 변경 시, app/services/v1/recommender.py 여기서만 작업할 것 recommendations 변경 X

from __future__ import annotations
from typing import List, Dict, Iterable, Optional
# from dataclasses import dataclass
from datetime import datetime, timezone
from app.core.config import settings

from app.models.enums import Category

from app.models.domain import (
    RoomRecommandRoomMeta,
    RoomRecommandUserMeta
)
# from app.processors.preprocessors import normalize_category
# -> json data의 전처리를 preproessors에서 할 것 인지.


class CategoryIndex:
    """
    문자열 카테고리를 정수 인덱스로 매핑
    - vocab: ['스터디', '운동', '독서', ...] 전체 카테고리 목록
    - index: {'스터디':0, '운동':1, ...}
    서버 기동 시 1회 구성하여 Recommender에 주입하는 방식을 권장
    """
    def __init__(self) -> None:
        vocab_list = [e.value for e in Category]
        self.index: Dict[str, int] = {cat: i for i, cat in enumerate(vocab_list)}
        self.dim: int = len(vocab_list)


class Recommender:
    """
    외부(엔드포인트)는 rank(), _rank_coldstart()만 호출
    - 비콜드스타트: 카테고리 유사도(B안)만 사용
    - 콜드스타트: popularity/recency 간단조합(예시)
    - 의존관계:
        * CategoryIndex: 카테고리 정수 인덱스/어휘집 관리
        * (선택) 전처리 유틸: 카테고리 문자열 표준화
        * 실제 데이터 소스(레포지토리/DAO)는 엔드포인트 측에서 주입하여 rank 또는 rank_coldstart에 전달
    """

    def __init__(self, cat_index: CategoryIndex) -> None:
        self.cat_index = cat_index

    def rank(
        self,
        user: RoomRecommandUserMeta,
        rooms: List[RoomRecommandRoomMeta],
        limit: int = settings.RECOMMANDS_LIMIT,
        now: Optional[datetime] = None,
    ) -> List[int]:

        """_summary_

        Returns:
            List[int] -> gatherings_id return
        """
        now = now or datetime.now(timezone.utc)

        # 콜드스타트 판정: 선호가 비어 있으면 콜드스타트
        # user_id가 존재하지 않을 떄, 콜드스타트
        if getattr(user, "is_not_authenticated", False) or not getattr(user, "preferred_categories", None):
            ranked = self._rank_coldstart(rooms, now)
            return ranked

        # 비콜드스타트: 카테고리 유사도(B안, 0/1)만 사용
        scored = []
        prefs_set = {Category._cat_name(p) for p in user.preferred_categories if p}

        for rm in rooms:
            cat = getattr(rm.category, "value", rm.category)
            cat_match = 0.8 if cat in prefs_set else 0.0

        # 나이(학번) 근접도 0~1 → 0.2 가중
            age_diff = abs(rm.host_age - user.user_age)
            age_term = max(0.0, 1 - (age_diff / 10.0)) * 0.2
            cat_match += age_term

            scored.append((rm, cat_match))

        scored.sort(key=lambda x: (x[1], x[0].room_id), reverse=True)

        return [x[0].room_id for x in scored][:limit]

    # --- coldstart 전용(예시) ---
    def _rank_coldstart(self, rooms: List[RoomRecommandRoomMeta], now: datetime, limit: int = 20) -> List[int]:
        def recency_norm(updated_at: Optional[datetime]) -> float:
            # 콜드스타트시 최신도 순
            if not updated_at:
                return 0.0
            delta = (now - updated_at).total_seconds()
            tau = 3 * 24 * 3600  # 3일
            import math
            return max(0.0, min(1.0, math.exp(-delta / tau)))

        def popularity_norm(current_member: int) -> float:
            # 콜드스타트시 인기도 순
            return max(0.0, min(1.0, current_member / 50.0))

        scored = []
        for rm in rooms:
            s = 0.6 * popularity_norm(rm.current_member) + 0.4 * recency_norm(rm.updated_at)
            scored.append((rm, s))

        scored.sort(key=lambda x: (x[1], x[0].room_id), reverse=True)

        return [rm.room_id for rm in scored][:limit]
