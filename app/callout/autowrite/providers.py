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
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "너는 건국대학교 학생들을 위한 모임 소개문 작성 보조 AI야. "
                        "사용자가 입력한 모임 정보와 키워드를 바탕으로 자연스럽고 간결한 소개문을 만들어줘. "
                        "500자 ~ 800자로 작성해야 해."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content

    def _build_prompt(self, info: dict) -> str:
        """사용자 입력 정보를 기반으로 프롬프트 생성."""
        return (
            f"모임 이름: {info['title']}\n"
            f"카테고리: {info['category']}\n"
            f"장소: {info['location']}\n"
            f"날짜 및 시간: {info['date_time']}\n"
            f"최대 인원: {info['max_participants']}명\n"
            f"키워드: {', '.join(info['keywords'])}\n"
        )
