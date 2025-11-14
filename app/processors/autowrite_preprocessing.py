from typing import List
from app.models.schemas import AutoWriteRequest
from app.models.domain import AutoWrite
from datetime import datetime


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


def mapping(req: AutoWriteRequest) -> AutoWrite:
    return AutoWrite(
        room_id=req.room_id,
        title=req.title,
        category=req.category,
        location=req.location,
        date_time=datetime.fromisoformat(req.date_time),
        keywords=req.keywords,
        max_participants=req.max_participants,
        gender_neutral=True,
        max_chars=800
    )
