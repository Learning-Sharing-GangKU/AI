# app/callout/registry.py
# 역할:
# - 외부 호출 클라이언트들을 싱글톤처럼 제공하는 간단한 레지스트리.
# - 엔드포인트/서비스에서 get_xlmr_client()만 호출하면 환경 설정에 맞게 초기화/재사용합니다.

from __future__ import annotations
import os
from typing import Optional
from app.callout.filter.xlmr_client import XLMRClient
from app.callout.http import HttpCaller
from app.core.config import settings


_XLMR_SINGLETON: Optional[XLMRClient] = None


def init_xlmr_client(
    *,
    base_url: Optional[str] = None,
    path: Optional[str] = None,
    api_key: Optional[str] = None,
) -> XLMRClient:
    """
    명시 초기화 진입점. 인자가 없으면 환경변수로 보충합니다.
    필수: base_url, path (없으면 ValueError)
    """
    global _XLMR_SINGLETON

    base_url = settings.XLMR_BASE_URL
    path = settings.XLMR_PATH
    api_key = settings.XLMR_API_KEY

    if not base_url or not path:
        raise ValueError("XLMR_BASE_URL 또는 XLMR_PATH가 설정되지 않았습니다.")

    http = HttpCaller()
    _XLMR_SINGLETON = XLMRClient(
        base_url=base_url,
        path=path,
        api_key=api_key,
        http=http
    )
    return _XLMR_SINGLETON


def get_xlmr_client() -> Optional[XLMRClient]:
    """
    XLMRClient 싱글톤을 반환합니다.
    - 환경변수 미설정 등으로 생성 실패 시 None 반환.
    """
    global _XLMR_SINGLETON
    if _XLMR_SINGLETON is not None:
        return _XLMR_SINGLETON
    try:
        _XLMR_SINGLETON = XLMRClient.from_env()
        return _XLMR_SINGLETON
    except Exception:
        return None
