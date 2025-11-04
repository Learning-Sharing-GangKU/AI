# app/models/schemas.py
# 팀과 세부 논의 후 다시 작성해햐함.
# 역할: 외부와 주고받는 API 계약(요청/응답)을 Pydantic 모델로 정의
#      FastAPI가 이 스키마로 자동 검증/문서화를 수행합니다.
# 사용처: app/api/v1/endpoints/* (컨트롤러에서 직접 import)


from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field


# ----- 추천 API -----
class RecommendByCategoryRequest(BaseModel):
    """
    기본적인 흐름 -> 단순하게 백에서는 user_id만 넘겨주면 된다. 내가 DB에서 user의 정보를 가져오면 되니깐
    DB에서 무엇은 가져와야하나(endpoint에서 가져오긴 함)
    <User>
    user_id
    student_id

    <User_interests>
    category_id
    """
    user_id: int = Field(..., description="사용자 식별자")

    # 기존: preferred_categories: conlist(str, min_items=0, max_items=3)

    # preferred_categories: Annotated[
    #     List[str], Field(min_items=0, max_items=3)
    # ] = Field(default_factory=list, description="선호 카테고리(최대 3개)")
    # local_time: Optional[str] = Field(default=None, description="ISO8601, 선택")
    # # 기존: conint(ge=1, le=100)
    # limit: Annotated[int, Field(ge=1, le=100)] = 20
    # page: Annotated[int, Field(ge=1)] = 1


class RecommendationItem(BaseModel):
    """서버 → 클라이언트: 개별 추천 항목."""
    gatherings_id: List[int]
    # -> 그냥 id만 보내고 끝낼거임

    # host_id:
    # category_id:
    # title: str
    # score: float
    # # 리스트 기본값은 default_factory로 생성
    # tags: List[str] = Field(default_factory=list)
    # region: Optional[str] = None
    # member_count: Optional[int] = None
    # thumbnail_url: Optional[str] = None


class RecommendationResponse(BaseModel):
    """
    AI -> BE
    내부 로직 정렬 후 gathering_id들만 리스트로 보내주면 된다.
    """
    """서버 → 클라이언트: 추천 결과 목록."""
    items: List[RecommendationItem] = Field(default_factory=list)
    total: Optional[int] = None
    page: int
    limit: int
    # dict 보다는 키/값 타입 지정
    debug: Optional[Dict[str, str]] = None


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
