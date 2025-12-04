# app/api/v1/endpoints/autowrity.py
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from app.models.schemas import AutoWriteRequest, AutoWriteResponse
from app.services.v1.autowrite import AutoWriteService
from app.processors.autowrite_preprocessing import mapping
from app.filters.v1.curse_detection_model import LocalCurseModel
from app.api.v1.deps import get_curse_model_dep

router = APIRouter(
    prefix="/gatherings"
)

"""
@router.post(
    "/intro/stream",
    summary="AI 기반 모임 소개문 스트리밍 생성",
    response_class=PlainTextResponse,
)
async def stream_autowrite(req: AutoWriteRequest, curse_model: LocalCurseModel = Depends(get_curse_model_dep)):
    # 실시간 전송
    domain_input = mapping(req, curse_model)
    if isinstance(domain_input, str):
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "FILTER_NOT_ALLOWED",
                    "message": (
                        f"[{domain_input}] 입력값에 부적절한 표현이 포함되어 있습니다."
                    )
                }
            }
        )

    service = AutoWriteService()

    async def token_stream():
        async for chunk in service.stream_intro(domain_input):
            try:
                yield chunk.encode("utf-8")
            except Exception:
                break

    return StreamingResponse(token_stream(), media_type="text/plain; charset=utf-8")
"""


@router.post(
    "/intro",
    summary="AI 기반 모임 소개문 생성",
    response_model=AutoWriteResponse,
)
async def generate_intro(
    req: AutoWriteRequest,
    curse_model: LocalCurseModel = Depends(get_curse_model_dep)
):
    """
    - profanity/욕설/금칙어 필터 적용
    - AI 생성 실패 시 FallbackWriter 적용
    - 최종 소개문을 문자열로 바로 반환
    """

    # ----------------------------------------------------------
    # 1) 필터링 및 도메인 매핑 (AutoWrite or 'title'/'keyword')
    # ----------------------------------------------------------
    domain_input = mapping(req, curse_model)

    if isinstance(domain_input, str):
        # domain_input == "title" or "keyword"
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "FILTER_NOT_ALLOWED",
                    "message": f"[{domain_input}] 입력값에 부적절한 표현이 포함되어 있습니다."
                }
            }
        )

    # 2) generate_intro() 실행
    service = AutoWriteService()

    try:
        response = await service.generate_intro(domain_input)  # AutoWriteResponse 반환
    except Exception as e:
        print("[ERROR] AutoWriteService.generate_intro 실패:", e)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "AI_GENERATION_FAILED",
                    "message": "AI가 소개문을 생성하지 못했습니다. 다시 시도해주세요."
                }
            }
        )

    # 3) 반환
    return response
