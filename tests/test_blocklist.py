# tests/test_blocklist.py
# 역할:
# - BlacklistMatcher 클래스가 blacklist.txt를 정상적으로 읽고,
#   텍스트 입력에 대해 금칙어 매칭을 잘 수행하는지 검증합니다.

import os
import pytest

from app.filters.v1.blocklistV0 import BlacklistMatcher

# 기본 블랙리스트 경로 (app/filters/v1/blacklist.txt)
BLACKLIST_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "app", "filters", "v1", "blacklist.txt"
)
BLACKLIST_PATH = os.path.abspath(BLACKLIST_PATH)


@pytest.fixture(scope="module")
def matcher():
    # 테스트용 matcher 인스턴스 생성
    return BlacklistMatcher(path=BLACKLIST_PATH, word_boundary=False)


def test_blocked_word(matcher):
    text = "이 새끼 뭐야"
    hits = matcher.scan(text)
    assert matcher.is_blocked(text) is True
    assert any("새끼" in h["match"] for h in hits)


def test_clean_text(matcher):
    text = "안녕하세요 반갑습니다"
    hits = matcher.scan(text)
    assert matcher.is_blocked(text) is False
    assert hits == []


def test_english_curse(matcher):
    text = "fuck you"
    hits = matcher.scan(text)
    assert matcher.is_blocked(text) is True
    assert any(h["category"] == "Toxic" for h in hits)


def test_multiple_hits(matcher):
    text = "씨발 같은 소리하네"
    hits = matcher.scan(text)
    categories = {h["category"] for h in hits}
    print("씨발 같은 소리하네, ", hits)
    assert "Toxic" in categories
    # assert "Sexual" in categories
    assert matcher.is_blocked(text) is True


def test_stats(matcher):
    stats = matcher.stats()
    # 최소한 Slur, Toxic, Sexual 같은 카테고리는 있어야 함
    assert any(cat in stats for cat in ["Slur", "Toxic", "Sexual"])
    # 단어 개수가 0은 아니어야 함
    assert all(count >= 1 for count in stats.values())
