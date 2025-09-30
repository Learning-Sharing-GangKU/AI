import pytest
from app.callout.autowrite.router import route_generate

# 샘플 데이터
sample_data = {
    "room_id": 123,
    "title": "보드게임 모임",
    "keywords": ["보드게임", "초보 환영", "기숙사 근처"],
    "category": "취미",
    "location": "건국대 기숙사 근처 카페",
    "date": "2025-09-20",
    "max_participants": 6,
    "max_chars": 500
}


@pytest.mark.parametrize("provider", ["mock"])
def test_route_generate(provider):
    prompt = "보드게임 모임 소개문 작성"
    result = route_generate(
        "mock",
        prompt,
        max_tokens=sample_data["max_chars"],
    )
    assert "[MOCKED RESPONSE]" in result


def test_local_intro():
    prompt = """
        당신은 모임 홍보 글을 작성하는 카피라이터입니다.
        아래 정보를 참고하여 자연스럽고 따뜻한 톤으로 소개문을 작성하세요.

        모임 이름: 보드게임 모임
        키워드: 보드게임, 초보 환영, 기숙사 근처
        카테고리: 취미
        장소: 건국대 기숙사 근처 카페
        날짜: 2025-09-20
        최대 인원: 6명

        소개문:
        """

    result = route_generate("local", prompt, max_tokens=100)

    print("\n--- Local HuggingFace 한국어 모델 결과 ---\n")
    print(result)

    assert isinstance(result, str)
    assert len(result) > 0

