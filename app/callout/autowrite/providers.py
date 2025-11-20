# app/callout/autowrite/providers.py
from openai import AsyncOpenAI
import os
from app.core.config import settings


class Provider:
    """
    OpenAI 비동기 클라이언트를 통한 모임 소개문 생성기.
    - generate_intro(): 완성된 문장 한 번에 반환
    - stream_intro(): 토큰 단위 스트리밍 반환
    """

    def __init__(self, model: str | None = None) -> None:
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("❌ OPENAI_API_KEY is not set")

        # 모델 선택: 환경변수 → 인자 → 기본값
        self.model = model or settings.OPENAI_MODEL
        self.client = AsyncOpenAI(api_key=api_key)

        print(f"[INIT] ✅ OpenAI Provider initialized with model: {self.model}")

    # ------------------------------------------------------------------
    # 1️⃣ 비스트리밍 모드 (완성문 한 번에 반환)
    # ------------------------------------------------------------------
    async def generate_intro(self, info: dict) -> str:
        """모임 정보를 기반으로 완성된 소개문을 한 번에 반환"""
        prompt = self._build_prompt(info)
        max_chars = info.get("max_chars", 800)
        max_tokens = max(1, int(max_chars / 2))

        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": f"너는 건국대학교 학생들을 위한 모임 소개문 작성 보조 AI야. "
                            f"입력된 정보를 바탕으로 자연스럽고 따뜻한 소개문을 {max_chars}자 이내로 작성해줘.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )

        text = resp.choices[0].message.content.strip()
        print(f"[PROVIDER] ✅ Completed intro ({len(text)} chars)")
        return text

    # ------------------------------------------------------------------
    # 2️⃣ 스트리밍 모드 (토큰 단위로 실시간 전송)
    # ------------------------------------------------------------------
    async def stream_intro(self, info: dict):
        """OpenAI SDK 버전 차이에 상관없이 안전하게 청크 단위 스트림을 yield"""
        prompt = self._build_prompt(info)
        max_chars = info.get("max_chars", 500)
        max_tokens = max(1, int(max_chars / 2))

        print("[PROVIDER] stream_intro open")

        async with self.client.chat.completions.stream(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": f"너는 건국대학교 학생들을 위한 모임 소개문 작성 보조 AI야. "
                               f"입력된 정보를 바탕으로 자연스럽고 따뜻한 소개문을 {max_chars}자 이내로 작성해줘.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        ) as stream:
            async for item in stream:
                print("[EVENT RAW]", type(item), getattr(item, "type", None), repr(item))
                yield str(item)
                """
                try:
                    # 최신 SDK (>=1.40): Event 타입
                    if hasattr(item, "type"):
                        if item.type in ("message.delta", "response.output_text.delta"):
                            delta = getattr(item, "delta", None)
                            content = getattr(delta, "content", None)
                            if content:
                                print("[STREAM] Δ", content[:30])
                                yield content
                        continue

                    # 구버전 SDK: ChatCompletionChunk 타입
                    for choice in getattr(item, "choices", []):
                        delta = getattr(choice, "delta", None)
                        content = getattr(delta, "content", None)
                        if content:
                            print("[STREAM] δ", content[:30])
                            yield content
                except Exception as e:
                    print("[STREAM WARN]", repr(e))
                    continue
                """
        print("[PROVIDER] stream closed")

    # ------------------------------------------------------------------
    # 3️⃣ 프롬프트 생성기
    # ------------------------------------------------------------------
    def _build_prompt(self, info: dict) -> str:
        """입력된 모임 정보를 자연스러운 문장으로 구성"""
        gender_text = (
            "성중립적 표현으로 작성해주세요."
            if info.get("gender_neutral", True)
            else "자연스럽게 작성해도 됩니다."
        )

        return (
            f"모임 이름: {info['title']}\n"
            f"카테고리: {info['category']}\n"
            f"장소: {info['location']}\n"
            f"날짜 및 시간: {info['date_time']}\n"
            f"최대 인원: {info['max_participants']}명\n"
            f"키워드: {', '.join(info['keywords'])}\n"
            f"{gender_text}\n"
        )
