# app/processors/autowrite_preprocessing.py
from typing import List, Union
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends

from app.models.schemas import AutoWriteRequest
from app.models.domain import AutoWrite
from app.filters.v1.curse_detection_model import LocalCurseModel
from app.filters.v1.blocklistV0 import BlacklistMatcher


# 공백 정규화
def normalize_ws(text: str) -> str:
    return " ".join(text.split()) if text is not None else ""


# 내부 키워드 생성
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


# 메인 매핑 함수
def mapping(
    req: AutoWriteRequest,
    curse_model: LocalCurseModel,
    blacklist: BlacklistMatcher = BlacklistMatcher(),
) -> Union[AutoWrite, str]:

    # 1) 정규화
    title_norm = normalize_ws(req.title)
    keyword_norms = [normalize_ws(k) for k in req.keywords]

    # ----------------------------------------------------------------------
    # 2) 블랙리스트(사전 기반) 탐지 - 제목
    # ----------------------------------------------------------------------
    bl_title_hits = blacklist.scan(title_norm)
    if bl_title_hits:
        return "title"

    # ----------------------------------------------------------------------
    # 3) 블랙리스트(사전 기반) 탐지 - 키워드
    # ----------------------------------------------------------------------
    for kw_norm in keyword_norms:
        bl_kw_hits = blacklist.scan(kw_norm)
        if bl_kw_hits:
            return "keyword"

    # ----------------------------------------------------------------------
    # 4) ML 기반 독성 모델 탐지
    # ----------------------------------------------------------------------
    threshold = 0.40

    # 제목 점수
    title_score = curse_model.predict(req.title)
    if title_score >= threshold:
        return "title"

    # 키워드 점수
    for kw in req.keywords:
        kw_score = curse_model.predict(kw)
        if kw_score >= threshold:
            return "keyword"

    # ----------------------------------------------------------------------
    # 5) 모든 필터 통과 → AutoWrite domain 모델로 매핑
    # ----------------------------------------------------------------------
    return AutoWrite(
        title=req.title,
        category=req.category,
        location=req.location,
        date=datetime.fromisoformat(req.date),
        keywords=req.keywords,
        capacity=req.capacity,
        gender_neutral=True,
        max_chars=800
    )
