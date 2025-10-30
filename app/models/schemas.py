# app/models/schemas.py
# 팀과 세부 논의 후 다시 작성해햐함.
# 역할: 외부와 주고받는 API 계약(요청/응답)을 Pydantic 모델로 정의
#      FastAPI가 이 스키마로 자동 검증/문서화를 수행합니다.
# 사용처: app/api/v1/endpoints/* (컨트롤러에서 직접 import)

from typing import List, Optional, Dict, Annotated, Literal
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
    gathering_id: int
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
    title: str = Field(..., min_length=1)
    purpose: str = Field(..., min_length=1)
    audience: str = Field(..., min_length=1)
    keywords: List[str] = Field(default_factory=list)
    tone: str = Field(default="친근하고 명확하게")

    # 기존: conint(ge=50, le=600)
    length: Annotated[int, Field(ge=50, le=600)] = 140


class AutoWriteResponse(BaseModel):
    description: str
    safety_flags: Optional[List[str]] = None
    used_model: Optional[str] = None
    prompt_version: Optional[str] = None
