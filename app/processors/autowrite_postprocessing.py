# app/processors/autowrite_postprocessing.py
# safe_strip - 불필요한 문자 제거
def safe_strip(text: str) -> str:

    if text is None:
        return ""
    return text.strip()


def clamp_length(text: str, max_chars: int) -> str:

    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars]