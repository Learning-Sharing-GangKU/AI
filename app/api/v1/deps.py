# app/api/v1/deps.py
from typing import Optional
from fastapi import Request, HTTPException
from app.services.v1.recommender import Recommender, CategoryIndex

from app.callout.filter.xlmr_client import XLMRClient
from app.filters.v1.curse_detection_model import LocalCurseModel


def get_curse_model_dep(request: Request) -> LocalCurseModel:
    m = getattr(request.app.state, "curse_model", None)
    if m is None:
        raise HTTPException(status_code=500, detail="Curse model not initialized.")
    return m


def get_xlmr_client_dep(request: Request) -> Optional[XLMRClient]:
    return getattr(request.app.state, "xlmr_client", None)


def get_recommender(request: Request) -> "Recommender":
    """
    서버 기동 시 app.state.recommender에 올려둔 서비스를 꺼내서 주입합니다.
    없으면 500으로 실패시켜 원인을 바로 알 수 있게 합니다.
    """
    recommender = getattr(request.app.state, "recommender", None)
    if recommender is None:
        raise HTTPException(status_code=500, detail="Recommender not initialized.")
    return recommender
