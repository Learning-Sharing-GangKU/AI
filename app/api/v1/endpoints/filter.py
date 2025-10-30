'''
filter 사용 시나리오
- <User.nickname>                    사용자 닉네임 생성 및 수정            -> blacklist+2tle/korean-curse-detection
- <User.description.keyword>         모임 소개문 생성 및 수정 시 키워드 전달  -> blacklist+2tle/korean-curse-detection
- <Reviews.comment>                  사용자 리뷰 작성                    -> blacklist+xlmr-large-toxicity-classifier
- <Gathering.description>            모임 소개문 생성 및 수정              -> blacklist+xlmr-large-toxicity-classifier
'''
# app/api/v1/endpoints/filter.py
# 역할:
#   - 텍스트 안전성 검사 엔드포인트를 제공합니다.
#   - 파이프라인: 전처리(normalize) → 블랙리스트 매칭 → 정책 라우팅 → 모델 호출(xlmr or curse) → 최종 판정.
#   - "어떤 모델을 쓸지" 결정은 전처리가 아닌 "정책 라우팅 레이어"에서 수행합니다.
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
#   - 모델 출력: score(0~1)와 label(or boolean)을 공통 포맷으로 수렴.
#   - 임계값은 시나리오별로 분리(닉네임 엄격, 리뷰/소개는 문맥 평가 기준).
# 엔드포인트:
#   - POST /api/v1/filter
#     요청: { "scenario": "nickname|review|gathering", "text": "..." }
#     응답: {
#       "allowed": bool,                   # 최종 허용 여부
#       "score": float
#       "matches": dict
#     }

from __future__ import annotations
from typing import Dict, Literal
from fastapi import APIRouter, HTTPException

# 외부 DTO
from app.models.schemas import FilterCheckRequest, FilterCheckResponse

# 1) 전처리기
from app.processors.filter_preprocessing import TextPreprocessor, PreprocessConfig
# 2) 블랙리스트 매칭기
from app.filters.v1.blocklistV0 import BlacklistMatcher

# 3) 모델 어댑터(인터페이스) - 실제 구현은 서비스 폴더에 두시는 것을 권장
#    - curse: 로컬 이진 욕설 모델(2tle/korean-curse-detection 등)
#    - xlmr : xlm-roberta-large toxicity 계열(외부 호출/로컬 중 택1)
from app.filters.v1.curse_detection_model import LocalCurseModel
from app.callout.filter.registry import get_xlmr_client

router = APIRouter()

# --------------------------- 싱글톤 ---------------------------
# 의존관계 -> 싱글톤으로 관리
_PREPROCESSOR = TextPreprocessor(PreprocessConfig())
_MATCHER = BlacklistMatcher(word_boundary=False, ignore_case=True, hot_reload=True)
_CURSE = LocalCurseModel()
_XLMR = None  # 나중에 실제 클라이언트로 교체

# --------------------------- 시나리오/정책 ---------------------------
ScenarioT = Literal["nickname", "review", "gathering", "keyword", "title"]


def _route_for_scenario(scenario: ScenarioT) -> Literal["curse", "xlmr"]:
    """
    시나리오에 따라 사용할 모델 경로를 결정
    - nickname, keyword, title: 이진 욕설 분류(curse)만 사용
    - review, gathering: 문맥 독성 분류(xlmr) 우선(미구현 시 curse 폴백)
    """
    if scenario in ("nickname", "keyword", "title"):
        return "curse"
    return "xlmr"


def _threshold_for(scenario: ScenarioT, route: Literal["curse", "xlmr"]) -> float:
    """
    시나리오/모델별 임계값을 분리
    """
    if route == "curse":
        # 닉네임/키워드는 오탐-미탐 균형을 고려해 다소 엄격
        return 0.6 if scenario in ("nickname", "keyword", "title") else 0.7
    if route == "xlmr":
        # 문맥형은 스코어 분포가 넓으므로 다소 높게
        return 0.8 if scenario in ("review", "gathering") else 0.7
    return 0.7

# =========================
# 엔드포인트
# =========================


@router.post("/filter/check", response_model=FilterCheckResponse)
def filter_check(req: FilterCheckRequest) -> FilterCheckResponse:
    """
    금칙어/비속어 필터 엔드포인트.
    요청: FilterCheckRequest(text, scenario, return_normalized?)
    응답: FilterCheckResponse(allowed, score, matches)
    """
    scenario_raw = getattr(req, "scenario", None)
    if scenario_raw is None:
        raise HTTPException(status_code=422, detail="scenario is required")
    scenario = scenario_raw  # Literal["nickname","keyword","review","gathering"]중에 반드시 하나.

    raw: str = req.text

    # 1) 전처리: 의미 변경 없이 표준화
    normalized_text: str = _PREPROCESSOR.preprocess(raw)

    # 2) 블랙리스트: 명시 단어 매칭 시 즉시 차단
    bl_hits = _MATCHER.scan(normalized_text)
    if bl_hits:
        # blacklist에 매칭 시 그냥 뒤도 안 돌아보고 바로 false 반환
        matches: Dict[str, object] = {
            "blacklist": bl_hits,
            "route": "blacklist_block",
            "threshold": None,
            "reason": "blacklist matched",
        }
        # 관례적으로 score=1.0 처리(운영 합의에 따라 조정 가능)
        return FilterCheckResponse(allowed=False, score=1.0, matches=matches)

    # 3) 시나리오 기반 라우팅
    route = _route_for_scenario(scenario)

    # 4) 모델 추론
    if route == "xlmr":
        if _XLMR is not None:
            # 실제 XLMR 연동 시:
            # out = _XLMR.predict(normalized)
            # {"score": float, "label": 0|1}
            # ml_score = float(out["score"])
            # 임시: 폴백 제거하고 XLMR 결과 사용
            print("hello")
        else:
            # XLMR fallback 정책
            out = _CURSE.predict(normalized_text)

    else:
        # curse 경로
        out = _CURSE.predict(normalized_text)

    # 모델 출력 통일 포맷 가정: {"score": float, "label": 0|1}
    ml_score: float = float(out["score"])

    # 5) 임계값 비교
    threshold: float = _threshold_for(scenario, "xlmr" if route == "xlmr" else "curse")
    allowed: bool = ml_score < threshold

    # 6) 외부 DTO로 매핑해 반환
    matches: Dict[str, object] = {
        "blacklist": [],  # 위에서 통과했으므로 없음
        "route": route,
        "threshold": threshold,
        "reason": f"scenario={scenario}, route={route}",
    }

    return FilterCheckResponse(
        allowed=allowed,
        score=ml_score,
        matches=matches,
    )
