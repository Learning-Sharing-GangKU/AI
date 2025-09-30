from .providers import generate_intro as openai_generate
from .mock_provider import generate_intro as mock_generate
from .huggingface_provider import generate_intro as hf_generate
from .local_provider import generate_intro as local_generate   # ✅ 추가


def route_generate(provider: str, prompt: str, max_tokens: int = 500) -> str:
    if provider == "openai":
        return openai_generate(prompt, max_tokens)
    if provider == "mock":
        return mock_generate(prompt, max_tokens)
    if provider == "huggingface":
        return hf_generate(prompt, max_tokens)
    if provider == "local":       # ✅ 로컬 provider 분기
        return local_generate(prompt, max_tokens)
    raise ValueError(f"Unknown provider: {provider}")
