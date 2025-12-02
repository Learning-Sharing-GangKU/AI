# app/api/v2/endpoints/recommendations.py
# 역할:
# - 추천 API HTTP 엔드포인트(컨트롤러).
# - 요청 스키마 검증 후, 서비스(app/services/recommender.py)의 Recommender.rank() 호출.
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from datetime import datetime, timezone
from app.api.v1.deps import get_recommender

from app.api.v2.deps import get_recommender_v1, get_recommender_v2

# 0. 전처리
from app.processors.recommand_preprocessing import (
    clustering_request_usermeta,
    to_room_meta_list
)

# 1. 외부 DTO
from app.models.schemas import (
    RecommendByClusteringModelRequest,
    RecommendationResponse,
)

# 2. 내부 DTO
from app.models.domain import (
    RoomRecommandUserMetaV1,
    RoomRecommandRoomMetaV1,

    RoomRecommandUserMetaV2
)

# 3. Recommender 서비스 인스턴스
#    - 실제 환경에선 DI(의존성 주입)로 바꿀 수 있습니다.
from app.services.v2.recommender import Recommender as v2_recommender

from app.services.v1.recommender import (
    CategoryIndex,
    Recommender as fallback_recommender
)

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="",
    tags=["recommendations"],
)


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="사용자 선호 기반 방 추천")
async def recommend(
    req: RecommendByClusteringModelRequest,
    recommender_v2: v2_recommender = Depends(get_recommender_v2),
    recommender_v1: fallback_recommender = Depends(get_recommender_v1),
) -> RecommendationResponse:
    """
    req로 들어온 RecommendByClusteringModelRequest (user_id + user cluster 지정해주기 위한 필드들이 존재.)
    1. user_id가 없는 경우 -> v1에서 했던 것처럼 coldstart진행
    2. user_id존재 -> gatherings_popularity에서 cluster당 인기 방 response
    """
    try:
        # 0. 요청 바디 로그
        logger.info(
            "POST /recommendations 요청 수신 user_id=%s preferred_categories=%s num_gatherings=%s",
            req.user_id,
            req.preferred_categories,
            len(req.gatherings) if req.gatherings else 0,
        )

        UserMetaV2 = clustering_request_usermeta(req)
        logger.info("V2 UserMeta 생성 완료: %s", UserMetaV2)

        items = recommender_v2.rank(
            user=UserMetaV2,
            now=datetime.now(timezone.utc),
        )
        logger.info("V2 rank 결과: %s", items)

        # fallback 정책
        if items is None:
            logger.info("V2에서 추천 결과가 없어 V1 fallback 경로로 진입합니다.")

            user = RoomRecommandUserMetaV1(
                user_id=req.user_id,
                preferred_categories=req.preferred_categories,
                user_age=req.user_age
            )

            rooms = to_room_meta_list(req.gatherings)
            logger.info("V1 UserMeta=%s, rooms 개수=%s", user, len(rooms))

            items = recommender_v1.rank(
                user=user,
                rooms=rooms,
                now=datetime.now(timezone.utc)
            )
            logger.info("V1 rank 결과: %s", items)

        logger.info("최종 추천 결과 items=%s", items)
        return RecommendationResponse(items=items)

    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        # 내부 오류는 500으로 래핑
        raise HTTPException(status_code=500,
                            detail=f"recommendation failed: {str(e)}")
