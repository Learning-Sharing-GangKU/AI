# app/processors/filter_postprocess.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from app.models.schemas import FilterCheckResponse

RouteT = Literal["curse", "xlmr", "blacklist_block"]


@dataclass(frozen=True)
class FilterDecision:
    """
    엔드포인트/서비스 레이어에서 만든 '원시 결과'를 담는 타입.
    - DTO(FilterCheckResponse)로 변환하기 전에 사용하는 내부 결과.
    """
    allowed: bool
    score: float
    route: RouteT
    threshold: Optional[float]
    blacklist: List[str]


def to_filter_check_response(decision: FilterDecision) -> FilterCheckResponse:
    """
    후처리(응답 매핑):
    - reason 제거
    - matches 포맷 통일
    """
    # matches: Dict[str, Any] = {
    #     "blacklist": decision.blacklist,
    #     "route": decision.route,
    #     "threshold": decision.threshold,
    # }

    return FilterCheckResponse(
        allowed=decision.allowed,
    )
