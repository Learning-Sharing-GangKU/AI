from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

# 외부 DTO
from app.core.exception import AppException, ErrorCode
from app.models.schemas import FilterCheckRequest, FilterCheckResponse

from app.api.v1.deps import get_curse_model_dep, get_xlmr_client_dep

# 모델 어댑터(인터페이스) - 실제 구현은 서비스 폴더에 두시는 것을 권장
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
async def filter_check(
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
        return await FilterService(curse=curse, xlmr=xlmr).check_async(req.text)
    except Exception as e:
        # 내부 오류는 500으로 래핑
        raise AppException(ErrorCode.FILTER_FAILED, str(e))
