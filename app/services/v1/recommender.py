'''

  # app/services/recommender.py
# 역할: 추천 점수 계산 중 cat_match(카테고리 유사도) 계산을 담당하는 유틸 함수들입니다.
# 가정: 사용자 선호 카테고리는 최대 3개, 방의 카테고리는 정확히 1개입니다.

from typing import Iterable, Dict, List, Optional
import math

class CategoryIndex:
    """
    문자열 카테고리를 정수 인덱스로 매핑합니다.
    - vocab: ['스터디', '운동', '독서', ...] 등 전체 카테고리 목록
    - index: {'스터디':0, '운동':1, ...}
    이 매핑은 서버 기동 시 1회 구성 후 메모리에 캐시하는 것을 권장합니다.
    """
    def __init__(self, vocab: Iterable[str]) -> None:
        self.vocab: List[str] = [v.strip() for v in vocab if v and v.strip()]
        self.index: Dict[str, int] = {cat: i for i, cat in enumerate(self.vocab)}
        self.dim: int = len(self.vocab)

    def get(self, cat: str) -> Optional[int]:
        return self.index.get(cat)


# ------------------------------
# A안: 단순 멤버십 매칭(권장, 직관적)
# ------------------------------
def cat_match_membership(user_prefs: Iterable[str], room_cat: str) -> float:
    """
    사용자가 고른 선호 카테고리 집합에 방 카테고리가 포함되면 1, 아니면 0을 반환합니다.
    - 장점: 해석이 매우 직관적이며, 가중합에 넣었을 때 의미가 명확합니다.
    - 단점: 선호 간 우선순위/강도 반영이 어렵습니다.
    """
    prefs_set = {p for p in user_prefs if p}
    if room_cat in prefs_set:
        return 1.0
    return 0.0


# --------------------------------------
# B안: 정통 L2 코사인(원-핫/다중-핫 기반)
# --------------------------------------
def _l2_norm(vec: List[float]) -> float:
    return math.sqrt(sum(x * x for x in vec))

def _l2_normalize(vec: List[float]) -> List[float]:
    n = _l2_norm(vec)
    if n == 0.0:
        return vec
    inv = 1.0 / n
    return [x * inv for x in vec]

def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    # 영벡터 처리
    if all(x == 0.0 for x in a) or all(y == 0.0 for y in b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = _l2_norm(a)
    nb = _l2_norm(b)
    denom = na * nb
    if denom == 0.0:
        return 0.0
    sim = dot / denom
    # 수치 안정화
    if sim < 0.0:
        sim = 0.0
    if sim > 1.0:
        sim = 1.0
    return sim

def cat_match_cosine_l2(user_prefs: Iterable[str], room_cat: str, cidx: CategoryIndex) -> float:
    """
    코사인 유사도(L2 정규화)로 cat_match를 계산합니다.
    - 사용자: 다중-핫 벡터(최대 3개 1로 세팅) → L2 정규화
    - 방: 원-핫 벡터 → L2 정규화
    - 일치 시 유사도 = 1 / sqrt(k), k는 사용자 선호 개수(3개면 ~0.577), 불일치 시 0
    """
    u = [0.0] * cidx.dim
    count = 0
    for p in user_prefs:
        idx = cidx.get(p)
        if idx is not None:
            u[idx] += 1.0
            count += 1
    u = _l2_normalize(u)

    v = [0.0] * cidx.dim
    ridx = cidx.get(room_cat)
    if ridx is not None:
        v[ridx] = 1.0
    v = _l2_normalize(v)

    return _cosine(u, v)


# -------------------------------------------------------
# C안: 확률 분포(L1=1) 내적 후 선택 개수로 스케일 → {0,1}
# -------------------------------------------------------
def cat_match_scaled_prob(user_prefs: Iterable[str], room_cat: str) -> float:
    """
    사용자 분포 p(선호 n개면 각 1/n)와 방 원-핫 e_r의 내적 p·e_r은 매치 시 1/n, 불일치 0입니다.
    여기에 n을 곱해 cat_match를 {0,1}로 맞춥니다.
    - 코사인 엄밀 정의는 아니지만, 내적 기반 점수로서 해석이 쉽고 매치=1을 보장합니다.
    """
    prefs = [p for p in user_prefs if p]
    n = len(prefs)
    if n == 0:
        return 0.0
    # 멤버십 검사
    return 1.0 if room_cat in set(prefs) else 0.0  # p·e_r * n과 동일한 결과
'''

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
from typing import List, Dict, Iterable, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.domain import (
    RoomMeta,
    UserProfile
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
    def __init__(self, vocab: Iterable[str]) -> None:
        vocab_list = [v.strip() for v in vocab if v and v.strip()]
        self.vocab: List[str] = vocab_list
        self.index: Dict[str, int] = {cat: i for i, cat in enumerate(vocab_list)}
        self.dim: int = len(vocab_list)

    def has(self, cat: str) -> bool:
        return cat in self.index


class Recommender:
    """
    외부(엔드포인트)는 rank(), _rank_coldstart()만 호출
    - 비콜드스타트: 카테고리 유사도(B안)만 사용
    - 콜드스타트: popularity/recency 간단 조합(예시)
    - 의존관계:
        * CategoryIndex: 카테고리 정수 인덱스/어휘집 관리
        * (선택) 전처리 유틸: 카테고리 문자열 표준화
        * 실제 데이터 소스(레포지토리/DAO)는 엔드포인트 측에서 주입하여 rank 또는 rank_coldstart에 전달
    """

    def __init__(self, cat_index: CategoryIndex) -> None:
        self.cat_index = cat_index
    
    def rank(
        self,
        user: UserProfile,
        rooms: List[RoomMeta],
        limit: int = 20,
        page: int = 1,
        now: Optional[datetime] = None,
    ) -> Tuple[List[Dict], Optional[int], Dict[str, str]]:
        now = now or datetime.now(timezone.utc)

        # 콜드스타트 판정: 선호가 비어 있으면 콜드스타트
        if not user.preferred_categories:
            ranked = self._rank_coldstart(rooms, now)
            return self._paginate(ranked, limit, page), None, {
                "strategy_version": "rec_v1",
                "weights_profile": "cat_only (coldstart uses popularity+recency)",
                "note": "coldstart path"
            }

        # 비콜드스타트: 카테고리 유사도(B안, 0/1)만 사용
        scored = []
        prefs_set = set([p for p in user.preferred_categories if p])
        for rm in rooms:
            cat_match = 1.0 if rm.category in prefs_set else 0.0  # B안: “확률 내적 + 스케일”과 동일 결과
            scored.append((rm, cat_match))

        scored.sort(key=lambda x: (x[1], x[0].room_id), reverse=True)

        items = [
            {
                "room_id": rm.room_id,
                "title": rm.title,
                "category": rm.category,
                "score": float(score),
                "region": rm.region,
                "member_count": rm.member_count,
            }
            for rm, score in scored
        ]
        return self._paginate(items, limit, page), None, {
            "strategy_version": "rec_v1",
            "weights_profile": "cat_only",
            "note": "non-coldstart path"
        }
    
    # coldstart를 나눌 것인지 아닌지 확정
    # --- coldstart 전용(예시) ---
    def _rank_coldstart(self, rooms: List[RoomMeta], now: datetime) -> List[Dict]:
        def recency_norm(updated_at: Optional[datetime]) -> float:
            if not updated_at:
                return 0.0
            delta = (now - updated_at).total_seconds()
            tau = 3 * 24 * 3600  # 3일
            import math
            return max(0.0, min(1.0, math.exp(-delta / tau)))

        def popularity_norm(member_count: int) -> float:
            return max(0.0, min(1.0, member_count / 50.0))

        scored = []
        for rm in rooms:
            s = 0.6 * popularity_norm(rm.member_count) + 0.4 * recency_norm(rm.updated_at)
            scored.append((rm, s))

        scored.sort(key=lambda x: (x[1], x[0].room_id), reverse=True)
        return [
            {
                "room_id": rm.room_id,
                "title": rm.title,
                "category": rm.category,
                "score": float(s),
                "region": rm.region,
                "member_count": rm.member_count,
            }
            for rm, s in scored
        ]

    # --- 공통 유틸 ---
    def _paginate(self, items: List[Dict], limit: int, page: int) -> List[Dict]:
        if limit <= 0: limit = 20
        if page <= 0: page = 1
        start = (page - 1) * limit
        end = start + limit
        return items[start:end]


