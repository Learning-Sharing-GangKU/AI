from .providers import generate_intro


def route_generate(provider: str, prompt: str, max_tokens: int = 500) -> str:
    if provider == "openai":
        return generate_intro(prompt, max_tokens)
    raise ValueError(f"Unknown provider: {provider}")
