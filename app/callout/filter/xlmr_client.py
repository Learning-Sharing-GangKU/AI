# app/callout/xlmr_client.py
# 역할:
# - 외부에 배치된 XLMR 독성 분류 서비스를 호출합니다.
# - HttpCaller를 사용해 타임아웃/재시도/서킷브레이커 정책을 공유합니다.
# - 반환을 {"score": float, "label": int} 표준 형식으로 통일합니다.

from __future__ import annotations

import os
import numpy as np
from typing import Dict, Any, Optional, List
from ..http import HttpCaller


class XLMRClient:
    """
    사용 방법:
        client = XLMRClient.from_env()
        out = client.predict("문장")   # {"score": 0.82, "label": 1}

    환경변수:
        XLMR_BASE_URL  (필수) 예: https://xlmr-provider.internal/api/v1
        XLMR_API_KEY   (선택) Authorization: Bearer <token>
        XLMR_TIMEOUT   (선택) 기본 1.5
        XLMR_RETRIES   (선택) 기본 2
        XLMR_CB_COOLDOWN_SEC (선택) 기본 10
        XLMR_PATH      (선택) 기본 "/classify"  (POST)
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 1.5,
        retries: int = 2,
        cb_cooldown_sec: int = 10,
        path: str = "/classify",
        http: Optional[HttpCaller] = None
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.path = path if path.startswith("/") else f"/{path}"
        self.http = http or HttpCaller(timeout=timeout, retries=retries, cb_cooldown_sec=cb_cooldown_sec)

    @classmethod
    def from_env(cls) -> "XLMRClient":
        base_url = os.getenv("XLMR_BASE_URL")
        if not base_url:
            raise RuntimeError("XLMR_BASE_URL is not set")
        api_key = os.getenv("XLMR_API_KEY")
        timeout = float(os.getenv("XLMR_TIMEOUT", "1.5"))
        retries = int(os.getenv("XLMR_RETRIES", "2"))
        cb = int(os.getenv("XLMR_CB_COOLDOWN_SEC", "10"))
        path = os.getenv("XLMR_PATH", "/classify")
        return cls(base_url=base_url, api_key=api_key, timeout=timeout, retries=retries, cb_cooldown_sec=cb, path=path)

    def predict(self, text: str) -> Dict[str, Any]:
        """
        입력 텍스트 1건의 독성 확률을 반환합니다.
        실패/서킷오픈 시 안전 폴백: {"score": 0.0, "label": 0}
        """
        if not text:
            print("not text")
            return {"score": 0.0, "label": 0}

        url = f"{self.base_url}{self.path}"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        resp = self.http.post_json(
            url,
            payload={"inputs": text},
            headers=headers)
        # http.post_json을 사용해, 해당 url로부터 응답을 받음
        if resp is None:
            return {"score": 0.0, "label": 0}

        data = np.array(resp.json()).flatten().tolist()
        print(data)
        score = self._extract_toxic_entry(data)

        return {"score": score['score'], "label": score['label']}

    @staticmethod
    def _extract_toxic_entry(data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        HuggingFace XLMR 결과 리스트 중 label이 'toxic'인 항목만 반환.
        없으면 None을 반환.
        """
        if not isinstance(data, list):
            return None
        for entry in data:
            if isinstance(entry, dict) and entry.get("label", "").lower() == "toxic":
                return entry
        return None
