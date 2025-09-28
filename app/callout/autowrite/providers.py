from .openai_client import get_client


def generate_intro(prompt: str, max_tokens: int = 500) -> str:
    client = get_client()
    resp = client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
        max_output_tokens=max_tokens,
        temperature=0.7
    )
    return resp.output_text.strip()
