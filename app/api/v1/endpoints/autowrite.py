"""모임 자동 소개문 생성 엔드포인트 (AI 서버)."""

from fastapi import APIRouter, HTTPException
from app.models.schemas import AutoWriteRequest, AutoWriteResponse
from app.services.v1.autowrite import AutoWriteService
from fastapi.responses import StreamingResponse, PlainTextResponse

router = APIRouter(
    prefix="/ai/v1/gatherings",
    tags=["AutoWrite"],
)


@router.post(
    "/intro",
    response_model=AutoWriteResponse,
    summary="AI 기반 모임 소개문 자동 생성",
)
async def generate_autowrite(req: AutoWriteRequest) -> AutoWriteResponse:
    """
    메인 서버에서 POST된 모임 정보를 받아 AI 모델을 통해 소개문을 생성합니다.

    처리 흐름:
    1 요청 데이터 검증
    2 AutoWriteService를 통해 전처리 + AI 호출 + 후처리 수행
    3 AutoWriteResponse 형태로 결과 반환

    실패 시 서비스 계층에서 fallback(기본 템플릿)을 제공합니다.
    """
    service = AutoWriteService()

    try:
        result = await service.generate_intro(req)
        return result

    except HTTPException:
        # FastAPI가 기본적으로 처리하도록 재전달
        raise

    except Exception as exc:
        # 예상치 못한 예외 발생 시
        raise HTTPException(
            status_code=500,
            detail=f"AI intro generation failed: {str(exc)}",
        )


@router.post(
    "/intro/stream",
    summary="AI 기반 모임 소개문 스트리밍 생성",
    response_class=PlainTextResponse,   # ✅ Swagger에서 JSON으로 인식 안 하게 함
)
async def stream_autowrite(req: AutoWriteRequest):
    """GPT가 생성하는 내용을 청크 단위로 실시간 전송"""
    service = AutoWriteService()

    async def token_stream():
        async for chunk in service.stream_intro(req):
            yield chunk.encode("utf-8")

    return StreamingResponse(token_stream(), media_type="text/plain; charset=utf-8")