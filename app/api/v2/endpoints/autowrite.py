"""모임 자동 소개문 생성 엔드포인트 (AI 서버)."""

from fastapi import APIRouter, HTTPException
from app.models.schemas import AutoWriteRequest, AutoWriteResponse
from app.services.v1.autowrite import AutoWriteService
from fastapi.responses import StreamingResponse, PlainTextResponse

router = APIRouter(
    prefix="/gatherings",
    tags=["AutoWrite"],
)


@router.post(
    "/intro",
    summary="AI 기반 모임 소개문 스트리밍 생성",
    response_class=PlainTextResponse,
)
async def stream_autowrite(req: AutoWriteRequest):
    """GPT가 생성하는 내용을 청크 단위로 실시간 전송"""
    service = AutoWriteService()

    async def token_stream():
        async for chunk in service.stream_intro(req):
            yield chunk.encode("utf-8")

    return StreamingResponse(token_stream(), media_type="text/plain; charset=utf-8")
