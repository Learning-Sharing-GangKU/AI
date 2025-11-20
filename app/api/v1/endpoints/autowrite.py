# app/api/v1/endpoints/autowrity.py
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse

from app.models.schemas import AutoWriteRequest, AutoWriteResponse
from app.services.v1.autowrite import AutoWriteService
from app.processors.autowrite_preprocessing import mapping
from app.filters.v1.curse_detection_model import LocalCurseModel
from app.api.v1.deps import get_curse_model_dep


router = APIRouter(
    prefix="/gatherings"
)


@router.post(
    "/intro/stream",
    summary="AI 기반 모임 소개문 스트리밍 생성",
    response_class=PlainTextResponse,
)
async def stream_autowrite(req: AutoWriteRequest, curse_model: LocalCurseModel = Depends(get_curse_model_dep)):
    """GPT가 생성하는 내용을 청크 단위로 실시간 전송"""
    domain_input = mapping(req, curse_model)
    if isinstance(domain_input, AutoWriteResponse):
        return JSONResponse(status_code=200, content=domain_input.dict())
    
    service = AutoWriteService()

    async def token_stream():
        async for chunk in service.stream_intro(domain_input):
            try:
                yield chunk.encode("utf-8")
            except Exception:
                break

    return StreamingResponse(token_stream(), media_type="text/plain; charset=utf-8")
