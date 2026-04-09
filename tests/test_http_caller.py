# flake8: noqa
# tests/test_http_caller.py
# 역할:
# - app/callout/http.py의 HttpCaller.post_json() 동작을 실제 클래스로 검증합니다.
# - 네트워크는 사용하지 않도록 httpx.Client.post를 monkeypatch로 가로채고,
#   실제 httpx.Response 객체를 만들어 반환/예외를 발생시킵니다.

import json
import time
import httpx
import pytest

from app.callout.http import HttpCaller


def test_post_json_success(monkeypatch):
    """
    시나리오:
      - 첫 시도에서 200 OK를 반환한다.
    기대:
      - post_json이 httpx.Response를 그대로 반환하고, JSON 내용이 일치한다.
    """
    caller = HttpCaller(timeout=0.5, retries=2, cb_cooldown_sec=5)

    def fake_post(self, url, json=None, headers=None):
        req = httpx.Request("POST", url)
        # httpx.Response를 실제로 생성
        return httpx.Response(status_code=200, request=req, json={"ok": True, "echo": json})

    monkeypatch.setattr(httpx.Client, "post", fake_post, raising=True)

    resp = caller.post_json("https://example.com/echo", payload={"a": 1})
    assert resp is not None
    assert isinstance(resp, httpx.Response)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "echo": {"a": 1}}


def test_post_json_retry_then_success(monkeypatch):
    """
    시나리오:
      - 1번째 호출: 503 (재시도 대상)
      - 2번째 호출: 200 OK
    기대:
      - 최종적으로 성공 Response 반환, 호출 횟수는 2회.
    """
    caller = HttpCaller(timeout=0.5, retries=2, cb_cooldown_sec=5)

    calls = {"n": 0}

    def fake_post(self, url, json=None, headers=None):
        calls["n"] += 1
        req = httpx.Request("POST", url)
        if calls["n"] == 1:
            return httpx.Response(status_code=503, request=req, json={"error": "temporary"})
        return httpx.Response(status_code=200, request=req, json={"ok": True})

    monkeypatch.setattr(httpx.Client, "post", fake_post, raising=True)

    resp = caller.post_json("https://example.com/echo", payload={"a": 1})
    assert resp is not None
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert calls["n"] == 2  # 재시도 1회 발생 확인


def test_post_json_circuit_open(monkeypatch):
    """
    시나리오:
      - 모든 시도에서 네트워크 예외(Timeout 등) 발생 → 서킷 오픈
      - 서킷 오픈 시간 내 재호출 시, post() 자체가 실행되지 않고 즉시 None 반환
    기대:
      - 첫 호출: None (재시도 모두 실패) + 서킷 오픈
      - 두 번째 호출: 바로 None, 그리고 post() 호출 횟수 증가 없음
    """
    caller = HttpCaller(timeout=0.1, retries=1, cb_cooldown_sec=10)

    calls = {"n": 0}

    def fake_post(self, url, json=None, headers=None):
        calls["n"] += 1
        # httpx가 던지는 타임아웃 예외를 실제로 발생
        raise httpx.ReadTimeout("timeout")

    monkeypatch.setattr(httpx.Client, "post", fake_post, raising=True)

    # 첫 호출: 재시도 후 실패 → None
    resp1 = caller.post_json("https://example.com/fail", payload={"x": 1})
    assert resp1 is None
    # 최소 2회(초기 + 재시도) 호출 시도했는지 확인
    assert calls["n"] >= 2

    # 서킷 오픈 상태에서 두 번째 호출: post()가 호출되지 않아야 함
    before = calls["n"]
    resp2 = caller.post_json("https://example.com/fail", payload={"x": 2})
    assert resp2 is None
    assert calls["n"] == before  # 호출 횟수 증가 없음(서킷이 막고 있음)
