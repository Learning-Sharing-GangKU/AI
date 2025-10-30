import os
from openai import AsyncOpenAI


class Provider:
    """OpenAI 기반 모임 소개문 생성 Provider."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate_intro(self, info: dict) -> str:
        """모임 정보를 기반으로 소개문 생성."""
        prompt = self._build_prompt(info)

        # max_chars 반영 (500~800자 제한)
        max_chars = info.get("max_chars", 500)
        max_tokens = int(max_chars / 2)  # 대략 문자 수 → 토큰 수 추정

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "너는 건국대학교 학생들을 위한 모임 소개문 작성 보조 AI야. "
                        "입력된 모임 정보를 바탕으로 자연스럽고 간결한 소개문을 만들어줘. "
                        f"글자 수는 약 {max_chars}자 이내로 작성해줘."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    def _build_prompt(self, info: dict) -> str:
        """사용자 입력 정보를 기반으로 프롬프트 생성."""
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
