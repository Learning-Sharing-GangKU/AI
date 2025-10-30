# flake8: noqa

# tests/test_xlmr_client.py
# 역할:
# - app/callout/xlmr_client.py의 XLMRClient.predict()를 실제 HttpCaller를 통해 테스트합니다.
# - 네트워크를 막기 위해 httpx.Client.post만 monkeypatch로 가로채,
#   httpx.Response를 실제로 만들어 반환/예외를 발생시킵니다.

import httpx
import os
import pytest
from app.callout.filter.xlmr_client import XLMRClient
from app.callout.filter.registry import get_xlmr_client

pytestmark = pytest.mark.integration
# python -m pytest -q tests/test_xlmr.py

# @pytest.mark.skipif(not os.getenv("XLMR_API_KEY"), reason="XLMR_API_KEY not set")
def test_xlmr_integration_real_call():
    client = get_xlmr_client()
    out = client.predict("this is a normal sentence")
    assert set(out.keys()) == {"score", "label"}
    assert 0.0 <= out["score"] <= 1.0

# def test_xlmr_client_predict_ok(monkeypatch):
    """
    시나리오:
      - HuggingFace Inference API가 정상 JSON 응답을 돌려준다.
      - 예시 응답: [{"label":"toxic","score":0.83}, {"label":"non_toxic","score":0.17}]
    기대:
      - predict()가 {"score": float, "label": 0|1} 형태로 반환.
    """
    client = XLMRClient(
        base_url="https://api-inference.huggingface.co",
        path="/models/textdetox/xlmr-large-toxicity-classifier",
        api_key="hf_dummy",
        timeout=1.0,
        retries=1,
        cb_cooldown_sec=5,
    )

    def fake_post(self, url, json=None, headers=None):
        req = httpx.Request("POST", url)
        # HF 일반 케이스 응답 샘플
        data = [{"label": "toxic", "score": 0.83}, {"label": "neutral", "score": 0.17}]
        return httpx.Response(status_code=200, request=req, json=data)

    monkeypatch.setattr(httpx.Client, "post", fake_post, raising=True)

    out = client.predict("안녕하세용")
    assert isinstance(out, dict)
    # assert out.get("meta", {}).get("status") == "ok"
    assert "score" in out and isinstance(out["score"], float)
    assert 0.0 <= out["score"] <= 1.0
    # assert out["score"] <= 0.5


# def test_xlmr_client_predict_unavailable(monkeypatch):
    """
    시나리오:
      - HttpCaller 내부 post가 타임아웃 예외를 던져 모든 재시도가 실패하고,
        XLMRClient.predict() 내부 로직에 따라 'unavailable' 폴백을 반환해야 한다.
    기대:
      - {"score":0.0, "label":0, "meta":{"status":"unavailable" 또는 유사}} 형태.
    """
    client = XLMRClient(
        base_url="https://api-inference.huggingface.co",
        path="/models/textdetox/xlmr-large-toxicity-classifier",
        api_key="hf_dummy",
        timeout=0.2,
        retries=1,
        cb_cooldown_sec=5,
    )

    def fake_post(self, url, json=None, headers=None):
        # httpx 예외를 실제로 발생시켜 HttpCaller가 None을 반환하게 유도
        raise httpx.ReadTimeout("timeout")

    monkeypatch.setattr(httpx.Client, "post", fake_post, raising=True)

    out = client.predict("정상 문장입니다")
    print(out)
    assert isinstance(out, dict)
    assert out["score"] == 0.0
    assert out["label"] == 0
    # assert out.get("meta", {}).get("status") in ("unavailable", "retry_exhausted", "circuit_open")
