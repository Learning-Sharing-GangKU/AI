# import datetime


def generate_intro(prompt: str, max_tokens: int = 500) -> str:
    """
    무료 테스트용 Mock Provider.
    OpenAI API 대신 단순히 프롬프트를 변형해서 결과 반환.
    """
    fake_intro = (
        "📌 [MOCKED RESPONSE]\n"
        f"입력된 프롬프트 앞 50자: {prompt[:500]}...\n"
        "이건 실제 AI 결과가 아니라 테스트용 가짜 응답입니다."
    )
    return fake_intro
