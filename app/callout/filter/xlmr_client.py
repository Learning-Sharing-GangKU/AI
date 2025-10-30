# app/callout/xlmr_client.py
# 역할:
# - 외부에 배치된 XLMR 독성 분류 서비스를 호출합니다.
# - HttpCaller를 사용해 타임아웃/재시도/서킷브레이커 정책을 공유합니다.
# - 반환을 {"score": float, "label": int} 표준 형식으로 통일합니다.

from __future__ import annotations

import os
from typing import Dict, Any, Optional

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
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.path = path if path.startswith("/") else f"/{path}"
        self.http = HttpCaller(timeout=timeout, retries=retries, cb_cooldown_sec=cb_cooldown_sec)

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
            return {"score": 0.0, "label": 0}

        url = f"{self.base_url}{self.path}"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        resp = self.http.post_json(url, payload={"text": text}, headers=headers)
        # http.post_json을 사용해, 해당 url로부터 응답을 받음
        if resp is None:
            return {"score": 0.0, "label": 0}

        data = resp.json()
        score = self._extract_score(data)
        label = 1 if score >= 0.5 else 0
        return {"score": float(score), "label": label}

    @staticmethod
    def _extract_score(data: Any) -> float:
        """
        외부 제공자 응답 스키마 다양성을 방어적으로 처리합니다.
        허용 예:
        1) [{"label":"toxic","score":0.82},{"label":"non_toxic","score":0.18}]
        2) [{"label":"LABEL_1","score":0.82},{"label":"LABEL_0","score":0.18}]
        3) {"toxic": 0.82, "non_toxic": 0.18}
        4) {"labels": [...위와 동일 배열...]}

        매칭 실패 시 0.0 반환.
        """
        try:
            if isinstance(data, dict) and "labels" in data:
                data = data["labels"]

            if isinstance(data, dict):
                if "toxic" in data and isinstance(data["toxic"], (int, float)):
                    return float(data["toxic"])
                if "LABEL_1" in data and isinstance(data["LABEL_1"], (int, float)):
                    return float(data["LABEL_1"])

            if isinstance(data, list) and data and isinstance(data[0], dict):
                best = None
                for d in data:
                    lab = str(d.get("label", "")).lower()
                    sc = float(d.get("score", 0.0))
                    if lab in ("toxic", "label_1", "1"):
                        best = max(best, sc) if best is not None else sc
                if best is not None:
                    return float(best)
        except Exception:
            pass
        return 0.0
