# app/callout/http.py
# 역할:
# - 외부 HTTP 호출 공통 로직(타임아웃, 재시도, 라이트 서킷브레이커)을 캡슐화합니다.
# - 동기 httpx.Client를 사용하여 간단히 구성합니다. (비동기 필요시 AsyncClient 버전 추가 가능)

from __future__ import annotations

import time
from typing import Optional, Dict, Any

import httpx


class HttpCaller:
    """
    공통 HTTP 호출자.
    - 타임아웃, 재시도, 라이트 서킷브레이커를 제공합니다.
    - 서킷이 열린 동안에는 즉시 폴백(호출 생략)합니다.
    """

    def __init__(self, timeout: float = 1.5, retries: int = 2, cb_cooldown_sec: int = 10) -> None:
        # timeout: 1.5 -> 1,5초 넘으면 타임아웃으로 간주할거임
        self.timeout = float(timeout)
        # retries: 2 -> 최대 2번 시도해보고 안되면,
        self.retries = max(0, int(retries))
        # 서킷브레이커가 열려 있을 시간.->10초 지나면 해당 서킷을 half open
        self._cb_cooldown_sec = int(cb_cooldown_sec)
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
            return None  # 서킷 오픈 중

        last_exc: Optional[Exception] = None

        for try_count in range(self.retries + 1):
            try:
                resp = self._client.post(url, json=payload, headers=headers or {})
                # 재시도 대상 상태코드: 5xx/408/429
                if resp.status_code >= 500 or resp.status_code in (408, 429):
                    last_exc = httpx.HTTPStatusError("retryable", request=resp.request, response=resp)
                    continue
                resp.raise_for_status()
                return resp
            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError, httpx.HTTPStatusError) as e:
                last_exc = e
                # 간단 백오프가 필요하면 여기서 time.sleep(0.1) 등 추가 가능
                continue
            except Exception as e:
                last_exc = e
                print(f"[HttpCaller] Unhandled error: {type(e).__name__}: {last_exc}")
                break

        # 모든 시도 실패 → 서킷 오픈 (일정시간 동안 호출을 차단해버림)
        self._cb_open_until = time.time() + self._cb_cooldown_sec
        return None
