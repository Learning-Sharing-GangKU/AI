# app/callout/registry.py
# 역할:
# - 외부 호출 클라이언트들을 싱글톤처럼 제공하는 간단한 레지스트리.
# - 엔드포인트/서비스에서 get_xlmr_client()만 호출하면 환경 설정에 맞게 초기화/재사용합니다.

from __future__ import annotations

from typing import Optional

from .xlmr_client import XLMRClient

_XLMR_SINGLETON: Optional[XLMRClient] = None


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
