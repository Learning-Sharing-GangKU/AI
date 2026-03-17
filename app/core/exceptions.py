# app/core/exceptions.py


class FilterNotAllowedError(Exception):
    """필터링 실패 시 발생하는 예외 (욕설/금칙어 탐지)"""

    def __init__(self, field: str):
        self.field = field
        super().__init__(f"[{field}] 입력값에 부적절한 표현이 포함되어 있습니다.")


class AIGenerationError(Exception):
    """AI 소개문 생성 + Fallback 모두 실패 시 발생하는 예외"""

    def __init__(self, cause: Exception | None = None):
        self.cause = cause
        super().__init__("AI가 소개문을 생성하지 못했습니다. 다시 시도해주세요.")
