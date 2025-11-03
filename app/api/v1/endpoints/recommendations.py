# app/api/v1/endpoints/recommendations.py
# 역할:
# - 추천 API HTTP 엔드포인트(컨트롤러).
# - 요청 스키마 검증 후, 서비스(app/services/recommender.py)의 Recommender.rank() 호출.
# - DB 연동 전 단계이므로, 예시용 RoomRepository 목을 사용합니다.

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone
from app.api.deps import get_recommender

# 1. 외부 DTO
from app.models.schemas import (
    RecommendByCategoryRequest,
    RecommendationItem,
    RecommendationResponse,
)

# 2. 내부 DTO
from app.models.domain import (
    RoomRecommandUserMeta,
    RoomRecommandRoomMeta
)

# 1) Recommender 서비스 인스턴스
#    - 실제 환경에선 DI(의존성 주입)로 바꿀 수 있습니다.
from app.services.v1.recommender import Recommender
router = APIRouter()


# -------------------------------------------------------
# 예시: 카테고리 어휘집(실전에서는 config/DB로부터 로드 권장)
# -------------------------------------------------------
# CATEGORY_VOCAB = ["스터디", "운동", "독서", "게임", "음악", "봉사", "여행"]

# 서버 기동 시점에 CategoryIndex 생성
# CAT_INDEX = CategoryIndex(CATEGORY_VOCAB)


# -------------------------------------------------------
# 예시: RoomRepository 목(실제론 DB/캐시에서 조회)
# -------------------------------------------------------
# 기능이 더 많아질 경우 Repository/* 따로 구현 요소 존재.
class RoomRepository:
    """
    실제 구현에서는 DB/검색엔진에서 조건에 맞는 방 목록을 불러옵니다.
    여기서는 예시 데이터를 반환하도록 목(MOCK)으로 구성합니다.
    """
    def list_rooms(self) -> List[RoomRecommandRoomMeta]:
        now = datetime.now(timezone.utc)
        return [
            RoomRecommandRoomMeta(
                                    room_id=1, category="스터디",
                                    member_count=12, updated_at=now),
            RoomRecommandRoomMeta(
                                    room_id=2, category="운동",
                                    member_count=8,  updated_at=now),
            RoomRecommandRoomMeta(
                                    room_id=3, category="독서",
                                    member_count=20, updated_at=now),
            RoomRecommandRoomMeta(
                                    room_id=4, category="게임",
                                    member_count=5,  updated_at=now),
            RoomRecommandRoomMeta(
                                    room_id=5, category="음악",
                                    member_count=7,  updated_at=now),
            RoomRecommandRoomMeta(
                                    room_id=6, category="봉사",
                                    member_count=3,  updated_at=now),
            RoomRecommandRoomMeta(
                                    room_id=7, category="여행",
                                    member_count=10, updated_at=now),
        ]


ROOM_REPO = RoomRepository()


# -------------------------------------------------------
# 엔드포인트: POST /recommendations
# -------------------------------------------------------
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
    2) (DB) 방 목록 조회
    3) Recommender.rank() 호출
    4) 결과를 RecommendationResponse로 직렬화하여 반환
    """
    try:
        # 1) 입력 검증은 Pydantic에 의해 선처리됨. 추가 규칙이 있으면 여기서 검증 !!!!!!!!!!!!!!!
        # 밑에 카테고리 갯수도 검증 예시임
        if len(req.preferred_categories) > 3:
            raise HTTPException(
                status_code=400,
                detail="preferred_categories는 최대 3개까지 허용됩니다."
                )

        # 2) 데이터 조회(예시)
        # db랑 연동될 시에 수정 요소 있음
        rooms = ROOM_REPO.list_rooms()

        # 3) 추천 서비스 호출 (수정: user DTO로 넘김)
        user = RoomRecommandUserMeta(
                user_id=req.user_id,
                preferred_categories=req.preferred_categories,
                class_user=req.class_user
                )

        items, total, debug = recommender.rank(
                            user=user,
                            rooms=rooms,
                            limit=req.limit,
                            page=req.page,
                            now=datetime.now(timezone.utc),
                            )

        # 4) DTO 변환: RecommendationItem 리스트로 변환
        # models/schemas 형식으로 변환한후 외부와 통신
        out_items: List[RecommendationItem] = [
            RecommendationItem(
                room_id=item["room_id"],
                title=item["title"],
                category=item["category"],
                score=item["score"],
                region=item["region"],
                member_count=item["member_count"],
                thumbnail_url=None
            )
            for item in items
        ]

        return RecommendationResponse(
            items=out_items,
            total=total,
            page=req.page,
            limit=req.limit,
            debug={
                "strategy_version": debug.get("strategy_version", "rec_v1"),
                "weights_profile": debug.get("weights_profile", "cat_only"),
                "note": debug.get("note", "")}
        )
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        # 내부 오류는 500으로 래핑
        raise HTTPException(status_code=500,
                            detail=f"recommendation failed: {str(e)}")
