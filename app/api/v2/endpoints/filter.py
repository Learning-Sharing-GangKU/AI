'''
filter 사용 시나리오
- <User.nickname>                    사용자 닉네임 생성 및 수정            -> blacklist + 2tle/korean-curse-detection
- <User.description.keyword>         모임 소개문 생성 및 수정 시 키워드 전달  -> blacklist + 2tle/korean-curse-detection
- <Gathering.tilte>                  모임 제목 생성 및 수정                -> blacklist + 2tle/korean-curse-detection

- <Reviews.comment>                  사용자 리뷰 작성                    -> blacklist + xlmr-large-toxicity-classifier
- <Gathering.description>            모임 소개문 생성 및 수정              -> blacklist + xlmr-large-toxicity-classifier
'''

# app/api/v1/endpoints/filter.py
# 역할:
#   - 텍스트 안전성 검사 엔드포인트를 제공합니다.
#   - 파이프라인: 전처리(normalize) → 블랙리스트 매칭 → 정책 라우팅 → 모델 호출(xlmr or curse) → 최종 판정.
#   - "어떤 모델을 쓸지" 결정은 전처리가 아닌 "정책 라우팅 레이어"에서 수행
#
# 의존관계:
#   - app/processors/text_preprocessing.py : TextPreprocessor (입력 표준화 담당)
#   - app/filters/v1/blocklistV0.py : BlacklistMatcher (금칙어 매칭 담당)
#   - app/filters/v1/curse_detection_model.py : LocalCurseModel (로컬 욕설 이진 분류 모델 어댑터)
#   - app/services/v1/xlmr_client.py (선택) : XLMR 어댑터(외부 호출 또는 로컬 로딩, 추후 연결)
#
# 설계 포인트:
#   - 전처리: 의미 변형 없이 표준화만 담당.
#   - 정책 라우터: 시나리오로 모델(xlmr, curse_detection) 선택.
#   - 모델 출력: score(0~1)을 공통 포맷으로 수렴.
#   - 임계값은 시나리오별로 분리(닉네임 엄격, 리뷰/소개는 문맥 평가 기준).
# 엔드포인트:
#     요청: { "scenario": "nickname|review|gathering", "text": "..." }
#     응답: {
#       "allowed": bool,                   # 최종 허용 여부
#       "score": float
#       "matches": dict
#     }

from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

# 외부 DTO
from app.models.schemas import FilterCheckRequest, FilterCheckResponse

from app.api.v1.deps import get_curse_model_dep, get_xlmr_client_dep

# 3) 모델 어댑터(인터페이스) - 실제 구현은 서비스 폴더에 두시는 것을 권장
#    - curse: 로컬 이진 욕설 모델(2tle/korean-curse-detection 등)
#    - xlmr : xlm-roberta-large toxicity 계열(외부 호출/로컬 중 택1)
from app.filters.v1.curse_detection_model import LocalCurseModel
from app.callout.filter.xlmr_client import XLMRClient
from app.services.v2.filter_service import FilterService


# =========================
# 엔드포인트
# =========================
router = APIRouter(
    prefix="/text",
    tags=["text_filter"],
)


@router.post("/filter", response_model=FilterCheckResponse)
def filter_check(
    req: FilterCheckRequest,
    curse: LocalCurseModel = Depends(get_curse_model_dep),
    xlmr: Optional[XLMRClient] = Depends(get_xlmr_client_dep)
) -> FilterCheckResponse:
    print("DEBUG type(xlmr) =", type(xlmr))
    """
    금칙어/비속어 필터 엔드포인트.
    요청: FilterCheckRequest(text, scenario)
    응답: FilterCheckResponse(allowed, score, matches)
    """
    try:
        return FilterService(curse=curse, xlmr=xlmr).check(req.text)
    except Exception as e:
        # 내부 오류는 500으로 래핑
        raise HTTPException(status_code=500,
                            detail=f"recommendation failed: {str(e)}")
