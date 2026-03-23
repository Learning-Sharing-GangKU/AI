import logging
# app/services/v1/autowrite.py
from datetime import datetime
from app.callout.autowrite.providers import Provider
from app.models.schemas import AutoWriteResponse
from app.models.domain import AutoWrite
from app.processors.autowrite_postprocessing import safe_strip, clamp_length
from app.core.exceptions import AIGenerationError
from types import AsyncGeneratorType
import inspect

logger = logging.getLogger(__name__)

class FallbackWriter:
    """AI 호출 실패 시 기본 안내문 생성"""

    def render_meeting_template(self, dto: AutoWrite) -> str:
        if isinstance(dto.date, datetime):
            date = dto.date.strftime("%Y년 %m월 %d일이고,")
        elif isinstance(dto.date, str):
            date = datetime.fromisoformat(dto.date).strftime("%Y년 %m월 %d일이고,")
        else:
            date = "미정"

        intro = f"🌟 안녕하세요! 『{dto.title}』 모임에 관심 가져주셔서 정말 반가워요! 🌟\n"

        part1 = (
            f"이번 모임은 {dto.category}에 흥미가 있거나 관련 경험을 나누고 싶은 분들을 위해 준비한 자리예요. "
            f"📌 일시는 {date} 📍 장소는 {dto.location}입니다. "
            "바쁜 일정 속에서도 잠시 시간을 내어 함께한다면, 분명 새로운 에너지와 즐거움을 얻으실 수 있을 거예요. ✨"
        )

        part2 = f"정원은 {dto.capacity}명으로 제한되어 있습니다! 😊 "
        if dto.gender_neutral:
            part2 += "성별이나 배경에 상관없이 누구나 환영하고 있으니, 부담 없이 오시면 됩니다."

        part3 = (
            f"『{dto.title}』 모임은 함께 웃고 공감하며 서로의 일상 이야기도 나눌 수 있는 특별한 공간이 되었으면 합니다. "
            "때로는 새로운 아이디어를 얻기도 하고, 때로는 그냥 편하게 대화하다가 스트레스를 풀기도 하죠. "
            "아마 오셔서 앉아 계시다 보면 ‘아, 오길 잘했다’라는 생각을 자연스럽게 하실 거예요. 💡"
        )

        part4 = (
            "혹시 아직도 고민하고 계신가요? 그렇다면 이렇게 생각해 보세요. "
            "이번 기회를 놓치면 또 언제 이런 자리를 만나게 될까요? 🕒 "
            "우리 삶은 늘 바쁘고 해야 할 일들은 끝이 없지만, 그 속에서도 잠시 멈춰서 "
            "새로운 사람들과 연결되는 경험은 오래도록 남습니다. "
            f"정원 {dto.capacity}명이라 금방 마감될 수 있으니, 지금 바로 신청하시는 걸 추천드려요! 🚀"
        )

        closing = (
            f"마지막으로, 여러분을 따뜻하게 맞이할 준비는 이미 다 되어 있습니다. "
            "누구보다도 반가운 마음으로 기다리고 있을게요. 🥳 "
            f"이번 『{dto.title}』 모임에서 꼭 뵐 수 있기를 바랍니다. "
            "그날 함께 웃고, 배우고, 또 좋은 인연을 만들어가요! 🙏"
        )

        return "\n\n".join([intro, part1, part2, part3, part4, closing])


class AutoWriteService:
    """AI 호출 및 실패 시 Fallback 템플릿 반환."""

    def __init__(self, provider: Provider) -> None:
        self.provider = provider
        self.fallback_writer = FallbackWriter()

    async def generate_intro(self, req: AutoWrite) -> AutoWriteResponse:
        """
        모임 소개문 자동 생성.
        - 요청(req)을 내부 도메인 객체로 변환 후 AI 호출 수행
        - 실패 시 fallback 템플릿 사용
        """

        logger.debug("generate_intro() called")
        info = vars(req)

        try:
            result = self.provider.generate_intro(info)

            logger.debug("provider.generate_intro() 시작")
            if inspect.isawaitable(result):
                text = await result
            elif inspect.isasyncgen(result):
                chunks = []
                async for chunk in result:
                    chunks.append(chunk)
                text = "".join(chunks)
            else:
                text = str(result)

        except Exception as ai_err:
            logger.warning(f"AI 생성 실패, fallback 시도: {ai_err}")
            try:
                text = self.fallback_writer.render_meeting_template(req)
            except Exception as fb_err:
                raise AIGenerationError(cause=fb_err) from fb_err

        cleaned = safe_strip(text)
        max_chars = getattr(req, "max_chars", 800)
        limited = clamp_length(cleaned, max_chars=max_chars)

        return AutoWriteResponse(
            intro=limited,
            aiversion="v1"
        )

    async def stream_intro(self, req: AutoWrite):
        """AI 스트리밍 모드"""
        logger.debug("stream_intro() called")
        info = vars(req)

        logger.debug("provider.stream_intro() 시작")

        gen = self.provider.stream_intro(info)

        logger.debug(f"provider.stream_intro() type: {type(gen)}")

        if not isinstance(gen, AsyncGeneratorType):
            logger.warning("provider.stream_intro() returned coroutine instead of generator — awaiting it once.")
            result = await gen
            logger.warning(f"stream result (non-streaming): {result[:100] if result else 'empty'}")
            yield result or ""
            return

        async for chunk in gen:
            logger.debug(f"chunk: {chunk[:30]}")
            yield chunk
