# app/models/schemas.py
# 팀과 세부 논의 후 다시 작성해햐함.
# 역할: 외부와 주고받는 API 계약(요청/응답)을 Pydantic 모델로 정의
#      FastAPI가 이 스키마로 자동 검증/문서화를 수행합니다.
# 사용처: app/api/v1/endpoints/* (컨트롤러에서 직접 import)

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, root_validator
from datetime import datetime

from app.models.enums import Category


# ----- 추천 API -----

class GatheringIn(BaseModel):
    """
    단일 모임(방) 후보 1건의 입력 스키마.
    """
    room_id: int = Field(..., gt=0, description="모임 식별자(양의 정수)")
    category: Category = Field(..., description="모임 카테고리(한국어 Enum)")
    host_age: int = Field(ge=0, le=2100, description="호스트 나이")
    capacity_member: int = Field(..., description="콜드스타트에서 사용하기 위한 용도, 인기순용")
    current_member: int = Field(..., description="콜드스타트에서 사용하기 위한 용도, 인기순용")
    updated_at: datetime = Field(..., description="콜드스타트에서 사용하기 위한 용도, 최신순용")


class RecommendByCategoryRequest(BaseModel):
    """
    Request (
        user_id: int
        preferred_categories: Enum???
        gatherings: List[dict] -> {"gathering_id: 1", "category": "운동", "host_std_year": 20}
    )
    """
    user_id: Optional[int] = Field(
        None, gt=0, description="사용자 식별자(로그인 이용자 시 int, 비로그인 이용자 시 None)"
    )
    preferred_categories: List[Category] = Field(
        default_factory=list,
        min_items=0, max_items=3,    # 리스트 길이 제약
        description="선호 카테고리(최대 3개)"
    )
    user_age: Optional[int] = Field(
        None, ge=20, le=100, description="사용자 나이(선택)"
    )
    gatherings: List[GatheringIn] = Field(
        ..., description="랭킹 대상 모임 후보 리스트"
    )


class RecommendationResponse(BaseModel):
    """
    AI -> BE
    내부 로직 정렬 후 RecommendationItem들만 리스트로 보내주면 된다.
    """
    """서버 → 클라이언트: 추천 결과 목록."""
    items: List[int] = Field(default_factory=list)
    # dict 보다는 키/값 타입 지정
    # debug: Optional[Dict[str, str]] = None


# ----- 금칙어/비속어 필터 API -----
class FilterCheckRequest(BaseModel):
    text: str = Field(..., min_length=1, description="검사 대상 텍스트")
    # 백에서 request body에서 받아서 갈거임
    scenario: Literal["nickname", "keyword", "review", "gathering", "title"] = Field(
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


# ----- 모임소개 자동생성(API) -----


class AutoWriteRequest(BaseModel):
    room_id: int = Field(..., description="모임 ID")
    title: str = Field(..., min_length=1, description="모임 이름")
    keywords: List[str] = Field(..., description="모임 키워드 리스트")
    category: str = Field(..., description="모임 카테고리")
    location: str = Field(..., description="모임 장소")
    date_time: str = Field(
        ...,
        description="모임 일정 (ISO 8601, 예: 2025-09-20)"
    )
    max_participants: int = Field(..., ge=1, description="최대 참가 인원")
    """
    gender_neutral: bool = Field(
        default=True,
        description="성중립 표현 여부"
    )
    max_chars: int = Field(
        default=500,
        ge=500,
        le=800,
        description="생성 글자 수 제한"
    )
    """


class AutoWriteResponse(BaseModel):
    room_id: int = Field(..., description="모임 ID")
    description: str = Field(..., description="생성된 모임 소개문")
    actual_length: Optional[int] = Field(
        default=None,
        description="생성된 텍스트 실제 길이"
    )
    gender_neutral_applied: Optional[bool] = Field(
        default=None,
        description="성중립 표현 적용 여부"
    )
    used_model: Optional[str] = Field(
        default=None,
        description="사용된 모델 이름"
    )
    prompt_version: Optional[str] = Field(
        default="intro_gen_v1",
        description="사용된 프롬프트 버전"
    )
