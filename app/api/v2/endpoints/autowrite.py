# app/api/v2/endpoints/autowrite.py
from fastapi import APIRouter, Depends

from app.models.schemas import AutoWriteRequest, AutoWriteResponse
from app.services.v1.autowrite import AutoWriteService
from app.processors.autowrite_preprocessing import mapping
from app.filters.v1.curse_detection_model import LocalCurseModel
from app.api.v1.deps import get_curse_model_dep, get_autowrite_service

router = APIRouter()


@router.post(
    "/intro",
    summary="AI 기반 모임 소개문 생성",
    response_model=AutoWriteResponse,
)
async def generate_intro(
    req: AutoWriteRequest,
    curse_model: LocalCurseModel = Depends(get_curse_model_dep),
    service: AutoWriteService = Depends(get_autowrite_service),
):
    """
    - profanity/욕설/금칙어 필터 적용
    - AI 생성 실패 시 FallbackWriter 적용
    - 최종 소개문을 문자열로 바로 반환
    """

    domain_input = mapping(req, curse_model)
    return await service.generate_intro(domain_input)
