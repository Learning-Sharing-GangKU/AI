# app/processors/preprocessing.py
from typing import List
from datetime import datetime

from app.models.schemas import AutoWriteRequest
from app.models.domain import AutoWrite

from app.filters.v1.blocklistV0 import BlacklistMatcher


# 공백 정규화
def normalize_ws(text: str) -> str:
    return " ".join(text.split()) if text is not None else ""


# 블랙리스트 매처 싱글톤
_MATCHER = BlacklistMatcher(hot_reload=True)


# 공통 텍스트 금칙어 필터링
def filter_text(text: str) -> str:

    if not text:
        return text

    cleaned = normalize_ws(text)

    hits = _MATCHER.scan(cleaned)
    if hits:   
        for h in hits:
            cleaned = cleaned.replace(h["match"], "")
        return normalize_ws(cleaned)
    return cleaned


# 키워드 전용 필터
def filter_keywords(keywords: List[str]) -> List[str]:
    safe_list: List[str] = []

    for kw in keywords:
        if not kw:
            continue

        cleaned = filter_text(kw)

        if cleaned: 
            safe_list.append(cleaned)

    return safe_list


def build_internal_keywords(title: str, keywords: List[str]) -> List[str]:
    base = [kw.strip() for kw in keywords if kw and kw.strip()]
    title_tokens = [t for t in title.split() if len(t) > 1]

    merged = base + title_tokens

    seen = set()
    deduped = []
    for kw in merged:
        if kw not in seen:
            seen.add(kw)
            deduped.append(kw)

    return deduped


def mapping(req: AutoWriteRequest) -> AutoWrite:
    safe_title = filter_text(req.title)
    safe_keywords = filter_keywords(req.keywords)
    final_keywords = safe_keywords

    return AutoWrite(
        room_id=req.room_id,
        title=safe_title,
        category=req.category,
        location=req.location,
        date_time=datetime.fromisoformat(req.date_time),
        keywords=final_keywords,
        max_participants=req.max_participants,
        gender_neutral=True,
        max_chars=800
    )
