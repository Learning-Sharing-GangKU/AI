# app/processors/preprocessing.py
from typing import List, Union
from datetime import datetime

from app.models.schemas import AutoWriteRequest
from app.models.domain import AutoWrite

from fastapi import APIRouter, HTTPException, Depends
from app.api.v1.deps import get_curse_model_dep, get_xlmr_client_dep
from app.filters.v1.curse_detection_model import LocalCurseModel
from app.models.schemas import AutoWriteResponse
from app.filters.v1.blocklistV0 import BlacklistMatcher


# 공백 정규화
def normalize_ws(text: str) -> str:
    return " ".join(text.split()) if text is not None else ""


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


def mapping(req: AutoWriteRequest, 
            curse_model: LocalCurseModel,
            blacklist: BlacklistMatcher = BlacklistMatcher(),
            ) -> Union[AutoWrite, AutoWriteResponse]:

    title_norm = normalize_ws(req.title)
    keyword_norms = [normalize_ws(k) for k in req.keywords]

    bl_title_hits = blacklist.scan(title_norm)
    if bl_title_hits:
        first = bl_title_hits[0]
        return AutoWriteResponse(
            room_id=req.room_id,
            filter_scenario="title",
            filter_allowed=False,
            description=f"제목에 금칙어 '{first['match']}'(카테고리: {first['category']})가 포함되어 있습니다.",
            actual_length=0,
            gender_neutral_applied=None,
            used_model="blacklist_v1",
            prompt_version="intro_gen_v1",
        )

    for kw in keyword_norms:
        bl_kw_hits = blacklist.scan(kw)
        if bl_kw_hits:
            first = bl_kw_hits[0]
            return AutoWriteResponse(
                room_id=req.room_id,
                filter_scenario="keyword",
                filter_allowed=False,
                description=f"키워드 '{first['match']}'(카테고리: {first['category']})가 금칙어 목록에 포함되어 있습니다.",
                actual_length=0,
                gender_neutral_applied=None,
                used_model="blacklist_v1",
                prompt_version="intro_gen_v1",
            )

    title_score = curse_model.predict(req.title)
    keyword_scores = [(kw, curse_model.predict(kw)) for kw in req.keywords]
    threshold = 0.40

    if title_score >= threshold:
        return AutoWriteResponse(
            room_id=req.room_id,
            filter_scenario="title",
            filter_allowed=False,
            description="제목에서 부적절한 표현이 탐지되었습니다.",
            actual_length=0,
            gender_neutral_applied=None,
            used_model=None,
            prompt_version="intro_gen_v1"
        )
    
    for kw, score in keyword_scores:
        if score >= threshold:
            return AutoWriteResponse(
                room_id=req.room_id,
                filter_scenario="keyword",
                filter_allowed=False,
                description=f"키워드 '{kw}'에서 부적절한 표현이 탐지되었습니다.",
                actual_length=0,
                gender_neutral_applied=None,
                used_model=None,
                prompt_version="intro_gen_v1"
            )

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
