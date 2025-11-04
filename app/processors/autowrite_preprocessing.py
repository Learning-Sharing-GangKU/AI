from typing import List


def normalize_ws(text: str) -> str:

    return " ".join(text.split()) if text is not None else ""


def build_internal_keywords(title: str, keywords: List[str]) -> List[str]:

    base = [kw.strip() for kw in keywords if kw and kw.strip()]
    title_tokens = [t for t in title.split() if len(t) > 1]
    merged = base + title_tokens
    # 중복 제거 preserving order
    seen = set()
    deduped: List[str] = []
    for kw in merged:
        if kw not in seen:
            seen.add(kw)
            deduped.append(kw)
    return deduped
