from app.callout.autowrite.providers import Provider


class Router:
    """Provider 라우터 (현재 기본 OpenAI Provider만 등록)."""

    def __init__(self) -> None:
        self.providers = {"default": Provider}

    def get_provider(self, name: str = "default") -> Provider:
        if name not in self.providers:
            raise ValueError(f"Unknown provider: {name}")
        return self.providers[name]()
