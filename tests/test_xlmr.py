# flake8: noqa

import os
import pytest

from app.callout.filter.registry import get_xlmr_client

pytestmark = pytest.mark.integration


def _env_ready() -> bool:
    return bool(os.getenv("XLMR_BASE_URL")) and bool(os.getenv("XLMR_PATH")) and (os.getenv("XLMR_API_KEY"))


@pytest.mark.skipif(not _env_ready(), reason="XLMR_* 환경변수 미설정")
def test_xlmr_real_call_normal_sentence():
    """
    정상 문장(비독성) 예시를 보냅니다.
    네트워크 가능 + API 키 유효 + 모델 응답 정상 시
    {"score": float, "label": 0|1} 를 받아야 합니다.
    """
    client = get_xlmr_client()
    assert client is not None, "get_xlmr_client()가 None입니다. 환경변수 또는 초기화를 확인하세요."

    out = client.predict("이 문장은 정상적인 문장입니다. 테스트용으로 전송합니다.")
    assert isinstance(out, dict)
    assert set(out.keys()) == {"score", "label"}
    assert isinstance(out["score"], float)
    assert out["score"] <= 0.5
    print(out)


@pytest.mark.skipif(not _env_ready(), reason="XLMR_* 환경변수 미설정")
def test_xlmr_real_call_toxic_sentence():
    """
    상대적으로 독성이 있을 법한 문구를 보냅니다.
    모델이 실제로 높은 score를 줄지 여부는 보장되지 않지만,
    최소한 통신이 되고, 스키마가 유지되는지 확인합니다.
    """
    client = get_xlmr_client()
    assert client is not None

    out = client.predict("니애미")
    assert isinstance(out, dict)
    assert set(out.keys()) == {"score", "label"}
    assert isinstance(out["score"], float)
    assert out["label"] == "toxic"
    assert out["score"] >= 0.5

    print(out)

'''
# 프로젝트 루트에서 실행
export PYTHONPATH="$PWD:$PYTHONPATH"

# 셸에서 바로 확인
python - << 'PY'
import os
print("XLMR_BASE_URL =", os.getenv("XLMR_BASE_URL"))
print("XLMR_PATH     =", os.getenv("XLMR_PATH"))
print("XLMR_API_KEY  =", os.getenv("XLMR_API_KEY"))
PY
'''
