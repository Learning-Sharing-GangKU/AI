# app/models/schemas.py
# 팀과 세부 논의 후 다시 작성해햐함.
# 역할: 외부와 주고받는 API 계약(요청/응답)을 Pydantic 모델로 정의
#      FastAPI가 이 스키마로 자동 검증/문서화를 수행합니다.
# 사용처: app/api/v1/endpoints/* (컨트롤러에서 직접 import)

from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, root_validator
from datetime import datetime

from app.models.enums import Category, UserStatus


# ----- 추천 API -----
class GatheringIn(BaseModel):
    """
    단일 모임(방) 후보 1건의 입력 스키마.
    """
    gatheringId: int = Field(..., gt=0, description="모임 식별자(양의 정수)")
    category: Category = Field(..., description="모임 카테고리(한국어 Enum)")
    hostAge: int = Field(ge=0, le=2100, description="호스트 나이")
    capacity: int = Field(..., description="콜드스타트에서 사용하기 위한 용도, 인기순용")
    participantCount: int = Field(..., description="콜드스타트에서 사용하기 위한 용도, 인기순용")
    createdAt: datetime = Field(..., description="콜드스타트에서 사용하기 위한 용도, 최신순용")


# ----- 추천 API request v1-----
class RecommendByCategoryRequest(BaseModel):
    """
    Request (
        userId: int
        preferredCategories: Enum
        gatherings: List[dict] -> {"gatheringId: 1", "category": "운동", "host_age": 20}
    )
    """
    userId: Optional[int] = Field(
        None, gt=0, description="사용자 식별자(로그인 이용자 시 int, 비로그인 이용자 시 None)"
    )
    preferredCategories: Optional[List[Category]] = Field(
        None,
        min_length=1,
        max_length=3,
        description="선호 카테고리(최대 3개)"
    )
    age: Optional[int] = Field(
        None, ge=20, le=100, description="사용자 나이(선택)"
    )
    gatherings: List[GatheringIn] = Field(
        ..., description="랭킹 대상 모임 후보 리스트"
    )


# ----- 추천 API request v2-----
class RecommendByClusteringModelRequest(BaseModel):
    """
    해당 schema의 사용처
    1. /api/ai/v2/recommendations로 왔을 때, 해당 유저의 cluster 식별 및 cluster predict를 하기 위함.
    2. /api/ai/v2/refresh/clustering로 왔을 때 list형식으로 나열 해 cluster를 초기화 할 때 사용(하루 1회)
    """
    userId: Optional[int] = Field(
        None, gt=0, description="사용자 식별자(로그인 이용자 시 int, 비로그인 이용자 시 None)"
    )
    preferredCategories: Optional[List[Category]] = Field(
        None,
        min_length=1,
        max_length=3,
        description="선호 카테고리(최대 3개)"
    )
    age: Optional[int] = Field(
        None, ge=20, le=100, description="사용자 나이(선택)"
    )
    enrollNumber: Optional[int] = Field(
        None, description="사용자 학번(선택)"
    )
    user_join_count: Optional[int] = Field(
        None, description="사용자의 모임 참여 횟수(선택)"
    )
    # 해당 유저의 cluster 정보를 미리 받기 위함.(없음 말고)
    cluster_id: Optional[int] = Field(
        None, gt=0, description="해당 user가 cluster가 존재하는지."
    )

    # V2 : user_id 존재하지않거나, clustering 아티팩트 존재 X
    # -> V1으로 보내서, 처리해야하기 위함 fallback
    gatherings: Optional[List[GatheringIn]] = None


class RecommendationResponse(BaseModel):
    """
    AI -> BE
    내부 로직 정렬 후 RecommendationItem들만 리스트로 보내주면 된다.
    """
    """서버 → 클라이언트: 추천 결과 목록."""
    items: List[int] = Field(default_factory=list)
    # dict 보다는 키/값 타입 지정
    # debug: Optional[Dict[str, str]] = None


# ----- cluster 최신화 -----
class ClusteringUserData(BaseModel):
    user_id: Optional[int] = Field(
        None, gt=0, description="사용자 식별자(로그인 이용자 시 int, 비로그인 이용자 시 None)"
    )
    preferred_categories: Optional[List[Category]] = Field(
        None,
        min_length=1,
        max_length=3,
        description="선호 카테고리(최대 3개)"
    )
    user_age: Optional[int] = Field(
        None, ge=20, le=100, description="사용자 나이(선택)"
    )
    user_enroll: Optional[int] = Field(
        None, description="사용자 학번(선택)"
    )
    user_join_count: Optional[int] = Field(
        None, description="사용자의 모임 참여 횟수(선택)"
    )


class ClusterRefreshRequest(BaseModel):
    """
    클러스터를 Refresh할 때 받을 외부 DTO
    유저들의 데이터를 RecommendByClusteringModelRequest를 리스트 형태로 받고
    해당 리스트를 토대로 cluster를 만든다.
    """
    users: List[ClusteringUserData]


class ClusterRefreshResponse(BaseModel):
    """
    클러스터 재학습 결과를 요약해서 반환하는 응답 모델입니다.
    - 실서비스용으로는 굳이 안 써도 되지만,
    운영/디버깅 시 현재 모델 상태를 확인하기 위해 유용합니다.
    """
    n_users: int = Field(..., description="이번 배치에 사용된 사용자 수")
    n_clusters: int = Field(..., description="실제로 사용된 군집 수(K)")
    inertia: float = Field(
        ...,
        description="K-means SSE(inertia) 값"
    )
    cluster_sizes: Dict[int, int] = Field(
        ...,
        description="각 cluster_id별로 속한 사용자 수. 예: {0: 30, 1: 25, ...}"
    )
# ----- cluster 최신화 -----


# ----- cluster당 선호 방 최신화 -----
class UserActionlog(BaseModel):
    user_id: Optional[int] = Field(
        None, gt=0, description="사용자 식별자(로그인 이용자 시 int, 비로그인 이용자 시 None)"
    )
    room_id: int = Field(
        ..., gt=0, description="모임 식별자(양의 정수)"
    )
    status: UserStatus


class PopularityRefreshRequest(BaseModel):
    """
    사용자들의 참여로그를 분석해
    각각의 군집당 어떤 방이 인기있는지 분석을 하기 위함.
    """
    log_list: List[UserActionlog]


class PopularityRefreshResponse(BaseModel):
    """
    군집별 인기 방 테이블을 재계산한 뒤,
    요약 정보를 반환하는 응답 모델입니다.
    """
    total_logs: int = Field(..., description="처리한 전체 로그 수")
    n_clusters: int = Field(..., description="인기 방이 계산된 클러스터 수")
    top_n: int = Field(..., description="각 클러스터별로 상위 몇 개까지 저장했는지")
    cluster_popularity: Dict[int, List[int]] = Field(
        ..., description="cluster_id -> [room_id1, room_id2, ...] 매핑"
    )
# ----- cluster당 선호 방 최신화 -----


# ----- 금칙어/비속어 필터 API -----
class FilterCheckRequest(BaseModel):
    text: str = Field(..., min_length=1, description="검사 대상 텍스트")
    # 백에서 request body에서 받아서 갈거임
    scenario: Literal["nickname", "keyword", "review", "description", "title"] = Field(
        ..., description="사용 시나리오"
    )


class FilterCheckResponse(BaseModel):
    # ok: bool
    # hits: List[str] = Field(default_factory=list)
    # normalized_text: Optional[str] = None

    allowed: bool
    # 아래는 내부 회의 후 확정
    score: float
    matches: dict
    scenario: Literal["nickname", "keyword", "review", "description", "title"] = Field(
        ..., description="금칙어 검출"
    )


# ----- 모임소개 자동생성(API) -----
class AutoWriteRequest(BaseModel):
    title: str = Field(..., min_length=1, description="모임 이름")
    keywords: List[str] = Field(..., description="모임 키워드 리스트")
    category: str = Field(..., description="모임 카테고리")
    location: str = Field(..., description="모임 장소")
    date: str = Field(
        ...,
        description="모임 일정 (ISO 8601, 예: 2025-09-20)"
    )
    capacity: int = Field(..., ge=1, description="최대 참가 인원")


class AutoWriteResponse(BaseModel):
    intro: str = Field(..., description="생성된 모임 소개문")
    aiversion: str = "v1"
