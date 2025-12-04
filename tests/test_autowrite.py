"""autowrite 엔드포인트 함수(generate_autowrite) 직접 테스트."""

import os
import sys
import pytest
from datetime import datetime
from dotenv import load_dotenv

# 경로 설정 (AI 폴더 상위 기준)
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# 환경변수 로드
load_dotenv()

from app.api.v1.endpoints.autowrite import generate_autowrite  # noqa: E402
from app.models.schemas import AutoWriteRequest  # noqa: E402


@pytest.mark.asyncio
async def test_generate_autowrite_direct() -> None:
    req = AutoWriteRequest(
        room_id=1,
        title="보드게임 모임",
        category="취미",
        location="건국대 기숙사 근처 카페",
        date_time=datetime(2025, 9, 20).isoformat(),
        max_participants=6,
        keywords=["보드게임", "초보 환영", "친목"],
        gender_neutral=True,
        max_chars=800,
    )

    response = await generate_autowrite(req)

    print("=== 생성된 소개문 ===")
    print(response.description)

    assert response.room_id == 1
    assert isinstance(response.description, str)
    assert len(response.description) <= req.max_chars
