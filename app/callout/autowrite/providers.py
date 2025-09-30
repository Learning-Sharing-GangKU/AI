from .openai_client import get_client 
"""
openai_client 안에 만든 get_client 함수를 불러와서, OpenAI SDK 클라이 언트를 가져옴
"""


def generate_intro(prompt: str, max_tokens: int = 500) -> str:
    client = get_client()
    resp = client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
        max_output_tokens=max_tokens,
        temperature=0.7
    )
    return resp.output_text.strip()
