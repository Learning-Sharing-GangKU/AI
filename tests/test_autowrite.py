"""generate_autowrite() 엔드포인트 전체 호출 테스트"""

import os
import pytest
from datetime import datetime
from dotenv import load_dotenv

# ✅ .env 로드
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

from app.api.v1.endpoints.autowrite import generate_autowrite  # noqa: E402
from app.models.schemas import AutoWriteRequest  # noqa: E402


@pytest.mark.asyncio
async def test_generate_autowrite_full() -> None:
    """
    FastAPI 내부 계층을 전부 거쳐서 AI 호출 테스트
    (실제 generate_autowrite() 함수 실행)
    """
    req = AutoWriteRequest(
        room_id=1,
        title="보드게임 모임",
        category="취미",
        location="건국대 기숙사 근처 카페",
        date_time=datetime(2025, 9, 20).isoformat(),
        max_participants=6,
        keywords=["보드게임", "초보 환영", "친목"],
    )

    response = await generate_autowrite(req)

    print("\n=== 생성된 소개문 ===\n")
    print(response.description)
    print(f"\n[모델] {response.used_model}, [길이] {response.actual_length}자\n")

    assert isinstance(response.description, str)
    assert len(response.description) > 100
