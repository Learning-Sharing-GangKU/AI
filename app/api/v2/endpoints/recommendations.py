# app/api/v2/endpoints/recommendations.py
# 역할:
# - 추천 API HTTP 엔드포인트(컨트롤러).
# - 요청 스키마 검증 후, 서비스(app/services/recommender.py)의 Recommender.rank() 호출.

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from datetime import datetime, timezone
from app.api.v1.deps import get_recommender

from app.models.schemas import RecommendByClusteringModelRequest, ClusterRefreshRequest
from app.services.v2.recommender import ClusterTrainer

# 1. 외부 DTO
from app.models.schemas import (
    RecommendByCategoryRequest,
    RecommendationResponse,
)

# 2. 내부 DTO
from app.models.domain import (
    RoomRecommandUserMeta
)

# 3. recommand 전처리 함수
from app.processors.recommand_preprocessing import (
    to_room_meta_list
)

# 1) Recommender 서비스 인스턴스
#    - 실제 환경에선 DI(의존성 주입)로 바꿀 수 있습니다.
from app.services.v2.recommender import Recommender


# -------------------------------------------------------
# 엔드포인트: POST /recommendations
# -------------------------------------------------------
router = APIRouter(
    prefix="",
    tags=["recommendations"],
)


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="사용자 선호 기반 방 추천")
async def recommend(req: RecommendByCategoryRequest,
                    recommender: Recommender = Depends(get_recommender),
                    ) -> RecommendationResponse:
    """
    호출 시점:
    - 클라이언트가 추천 목록을 요청할 때마다 실행됩니다.

    처리 흐름:
    1) 요청 스키마 검증(Pydantic 자동)
    2) RecommendByCategoryRequest에서 방 목록 받음
    3) Recommender.rank() 호출
    4) 결과를 RecommendationResponse로 직렬화하여 반환
    """
    try:
        # 1) 입력 검증은 Pydantic에 의해 선처리됨. 추가 규칙이 있으면 여기서 검증 !!!!!!!!!!!!!!!
        # 밑에 카테고리 갯수도 검증 예시임
        if len(req.preferred_categories) > 3:
            raise HTTPException(
                status_code=400,
                detail="preferred_categories는 최대 3개까지 허용됩니다.")

        # 2) req로 날라온 gatherings 목록들을 전처리 함수에 넣어 내부 DTO인 [RoomRecommandRoomMeta]로 변환
        rooms = to_room_meta_list(req.gatherings)

        # 3) 추천 서비스 호출 (수정: user DTO로 넘김)
        user = RoomRecommandUserMeta(
            user_id=req.user_id,
            preferred_categories=req.preferred_categories,
            user_age=req.user_age)

        items = recommender.rank(
            user=user,
            rooms=rooms,
            now=datetime.now(timezone.utc),)

        # 4) DTO 변환: RecommendationItem 리스트로 변환
        # models/schemas 형식으로 변환한후 외부와 통신
        return RecommendationResponse(items=items)

    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        # 내부 오류는 500으로 래핑
        raise HTTPException(status_code=500,
                            detail=f"recommendation failed: {str(e)}")
