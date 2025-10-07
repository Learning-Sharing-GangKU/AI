import sys
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# 현재 파일 기준으로 상위 폴더(AI)를 Python path에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# .env 파일 로드
load_dotenv()

from app.callout.autowrite.router import Router  # noqa: E402


async def main() -> None:
    """사용자 입력 기반으로 모임 소개문을 생성."""
    router = Router()
    provider = router.get_provider()

    # ✅ 사용자가 모임 생성 시 입력하는 정보
    meeting_info = {
        "title": "보드게임 모임",
        "category": "취미",
        "location": "건국대 기숙사 근처 카페",
        "max_participants": 6,
        "date_time": datetime(2025, 9, 20, 18, 0).isoformat(),
        "keywords": ["보드게임", "초보 환영", "친목"],
    }

    # ✅ Provider로 데이터 전달 (프롬프트 구성은 Provider에서 처리)
    intro = await provider.generate_intro(meeting_info)

    print("=== 생성된 소개문 ===")
    print(intro)


if __name__ == "__main__":
    asyncio.run(main())
