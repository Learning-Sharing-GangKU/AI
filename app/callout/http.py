# app/callout/http.py
# 역할:
# - 외부 HTTP 호출 공통 로직(타임아웃, 재시도, 라이트 서킷브레이커)을 캡슐화합니다.
# - 동기 httpx.Client를 사용하여 간단히 구성합니다. (비동기 필요시 AsyncClient 버전 추가 가능)

from __future__ import annotations

import time
import logging
from typing import Optional, Dict, Any
from app.core.config import settings
import httpx

logger = logging.getLogger("app.http")


class HttpCaller:
    """
    공통 HTTP 호출자.
    - 타임아웃, 재시도, 라이트 서킷브레이커를 제공합니다.
    - 서킷이 열린 동안에는 즉시 폴백(호출 생략)합니다.
    """

    def __init__(self) -> None:
        # timeout: 넘으면 타임아웃으로 간주할거임
        self.timeout = float(settings.XLMR_TIMEOUT)
        # retries: 2 -> 최대 2번 시도해보고 안되면,
        self.retries = max(0, int(settings.XLMR_RETRIES))
        # 서킷브레이커가 열려 있을 시간. -> 5초 지나면 해당 서킷을 half open
        self._cb_cooldown_sec = int(settings.XLMR_CB_COOLDOWN_SEC)
        self._cb_open_until: float = 0.0  # 서킷 오픈 종료 시각(epoch sec)

        self._client = httpx.Client(timeout=self.timeout)

    def post_json(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[httpx.Response]:
        """
        POST JSON 요청을 보냅니다.
        - 성공: httpx.Response 반환
        - 재시도 실패/서킷오픈: None 반환
        """
        now = time.time()
        if now < self._cb_open_until:
            logger.warning("[HttpCaller] Circuit OPEN → skip request to %s (open_until=%.0f, now=%.0f)", url, self._cb_open_until, now)
            return None  # 서킷 오픈 중

        last_exc: Optional[Exception] = None

        for try_count in range(1, self.retries + 2):
            try:
                resp = self._client.post(url, json=payload, headers=headers or {})
                # 재시도 대상 상태코드: 5xx/408/429
                status_code = resp.status_code
                if status_code >= 500 or status_code in (408, 429):
                    last_exc = httpx.HTTPStatusError("retryable", request=resp.request, response=resp)
                    logger.warning("[HttpCaller] Retryable status %s (attempt=%d/%d) url=%s body=%s", status_code, try_count, self.retries + 1, url, _peek(resp))
                    continue

                # 비재시도 4xx는 여기서 바로 반환(호출자에게 이유를 보여주자)
                if 400 <= status_code < 500:
                    logger.error("[HttpCaller] Non-retryable 4xx %s (attempt=%d) url=%s body=%s", status_code, try_count, url, _peek(resp))
                    return resp

                return resp

            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
                last_exc = e
                logger.warning("[HttpCaller] Network error (attempt=%d/%d) url=%s err=%r", try_count, self.retries + 1, url, e)
                continue

            except httpx.HTTPStatusError as e:
                last_exc = e
                logger.warning("[HttpCaller] HTTPStatusError caught (attempt=%d/%d) url=%s err=%r", try_count, self.retries + 1, url, e)

            except Exception as e:
                last_exc = e
                logger.exception("[HttpCaller] Unhandled error url=%s", url)
                break

        # 모든 시도 실패 → 서킷 오픈 (일정시간 동안 호출을 차단해버림)
        self._cb_open_until = time.time() + self._cb_cooldown_sec
        logger.error("[HttpCaller] All retries failed. Circuit OPEN for %ds. last_exc=%r", self._cb_cooldown_sec, last_exc)
        return None


def _peek(resp: httpx.Response, limit: int = 200) -> str:
    """응답 바디 일부만 잘라서 로그에 찍습니다(민감정보 과다 노출 방지)."""
    try:
        txt = resp.text
        return (txt[:limit] + "...") if len(txt) > limit else txt
    except Exception:
        return "<body-unreadable>"
