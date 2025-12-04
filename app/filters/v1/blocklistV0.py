# flake8: noqa
# app/filters/v1/blocklistV0.py
# 역할:
#   - blacklist.txt(카테고리 주석 포함)를 읽어, 금칙어 매칭을 수행하는 모듈입니다.
#   - TextPreprocessor(전처리) 이후의 문자열을 입력으로 받아 scan()을 통해 매칭 결과를 반환합니다.
#   - 엔드포인트에서는 전처리 -> 본 블랙리스트 매칭 -> (옵션) ML 순서로 사용합니다.
#
# 의존관계:
#   - 파일: app/filters/v1/data/blacklist.txt
#     - 카테고리 헤더: "## ...Slur..." 같은 주석 라인을 만나면 해당 구간 단어를 그 카테고리에 할당
#     - 빈 줄/주석 라인은 무시
#
# 제공 기능:
#   - BlacklistMatcher.scan(text) -> List[dict]
#       [{"category": str, "match": str, "start": int, "end": int}, ...]
#   - BlacklistMatcher.is_blocked(text) -> bool
#   - 핫리로드: 파일 mtime 변화를 감지하여 자동 재로딩(동시성 안전)
#   - 단어 경계(word boundary) 옵션: 한국어/영어 혼용 서비스 특성상 기본 False 권장
#
# 사용 타이밍:
#   - FastAPI 엔드포인트에서 요청 수신 → 전처리(normalize) → 본 모듈로 scan() 호출
#   - 매칭 결과가 있으면 즉시 차단(allowed=False) 반환

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Pattern

# 기본 경로(서비스 루트 기준). 필요 시 환경변수/설정으로 주입 가능.
_DEFAULT_BLACKLIST_PATH = os.getenv(
    "BLACKLIST_PATH",
    "app/filters/v1/blacklist.txt",
)


@dataclass
class MatchItem:
    category: str
    match: str
    start: int
    end: int


class BlacklistMatcher:
    """
    금칙어 매칭 클래스.

    - 파일 포맷:
        ## =========================
        ## 1. Slur / ...
        ## =========================
        병신
        미친놈
        ...

        (카테고리 헤더는 "##" 로 시작하는 라인. 그 이후 단어들은 해당 카테고리에 속함)
        (빈 줄, '#' 또는 '##'로 시작하는 주석 라인은 무시)

    - 초기화 파라미터
        hot_reload: bool
            요청 시마다 mtime을 확인해 변경되었으면 자동 재로딩(운영에서 편리)
        path: str
            blacklist.txt 경로(기본값은 v1/data/blacklist.txt)

    - 스레드 안전:
        _lock 으로 로딩/갱신 보호.
    """

    def __init__(
        self,
        path: str = _DEFAULT_BLACKLIST_PATH,
        hot_reload: bool = True,
    ) -> None:
        self._path = path
        self._hot_reload = hot_reload

        self._lock = threading.RLock()
        self._mtime: Optional[float] = None

        # 내부 상태
        self.curse_categories: Dict[str, List[str]] = {}     # 카테고리 -> [단어...]
        self._patterns: Dict[str, Pattern[str]] = {}    # 카테고리 -> 컴파일된 정규식
        # self._patterns -> 단순하게 for문만 돌리면 너무 느리다 -> 정규식으로 컴파일하고 matching시 훨씬 빠른 결과를 얻을 수 있음

        self._load_and_build()  # 초기 로드

    # ---------------- 내부: 로드/빌드 ----------------
    def _load_and_build(self) -> None:
        """blacklist.txt를 읽고 카테고리별 단어 목록과 정규식을 빌드합니다. -> 속도 더 빠름"""
        with self._lock:
            words_by_cat = self._parse_file(self._path)
            patterns = self._compile_patterns(words_by_cat)

            self.curse_categories = words_by_cat
            self._patterns = patterns
            try:
                self._mtime = os.path.getmtime(self._path)
            except OSError:
                self._mtime = None

    def _maybe_reload(self) -> None:
        """hot_reload=True 일 때, 파일 mtime이 바뀌면 자동 재로딩."""
        if not self._hot_reload:
            return
        try:
            m = os.path.getmtime(self._path)
        except OSError:
            return
        if self._mtime is None or m != self._mtime:
            self._load_and_build()

    @staticmethod
    def _parse_file(path: str) -> Dict[str, List[str]]:
        """
        blacklist.txt를 파싱하여 {카테고리: [단어...]} 딕셔너리를 반환.
        - '##'로 시작하는 라인을 카테고리 헤더로 간주.
        - 그 외, 공백/주석(#) 라인은 무시.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Blacklist file not found: {path}")

        words_by_cat: Dict[str, List[str]] = {}
        current_cat = "default"

        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()

                # 빈 줄 무시
                if not line:
                    continue

                # 카테고리 헤더 (## ...)
                if line.startswith("##"):
                    # "## 1. Slur / ..." 같은 라인 전체를 카테고리 키로 사용하되,
                    # 사람이 읽기 쉬운 간단 키도 선호하면 여기서 정규화 가능.
                    current_cat = BlacklistMatcher._normalize_category_header(line)
                    words_by_cat.setdefault(current_cat, [])
                    continue

                # 주석(# ...) 무시 (단, 카테고리 헤더가 아니라면)
                if line.startswith("#"):
                    continue

                # 실제 단어 라인
                words_by_cat.setdefault(current_cat, []).append(line)

        return words_by_cat

    @staticmethod
    def _normalize_category_header(line: str) -> str:
        """
        '## 1. Slur / ...' 같은 헤더 라인을 카테고리 키로 정규화합니다.
        - 선행 '#' 제거, '숫자.' 프리픽스 제거, 공백 정리
        """
        s = line.lstrip("#").strip()
        s = re.sub(r"^[0-9]+\.\s*", "", s)  # '1. ' 제거
        s = re.sub(r"\s+", " ", s)          # 공백 정규화
        return s if s else "default"
    
    def _compile_patterns(self, words_by_cat: Dict[str, List[str]]) -> Dict[str, Pattern[str]]:
        """
        카테고리별 단어 리스트를 하나의 정규식으로 컴파일합니다.
        - 기본은 부분 매칭(단어 경계 미사용). 필요 시 경계 추가 로직 확장 가능.
        """
        patterns: Dict[str, Pattern[str]] = {}
        flags = re.IGNORECASE  # 영문 섞일 수 있어 대소문자 무시

        for cat, words in words_by_cat.items():
            terms = [re.escape(w) for w in words if w]
            if not terms:
                # 매칭 불가능한 더미 패턴
                patterns[cat] = re.compile(r"(?!x)x")
                continue

            body = "|".join(terms)
            regex = rf"({body})"  # group(1)에 실제 매칭 단어를 담도록 캡처
            patterns[cat] = re.compile(regex, flags)

        return patterns
    
    def scan(self, text: str) -> List[Dict[str, object]]:
        """
        텍스트에서 카테고리별 매칭 결과를 반환합니다.
        예:
            [{"category":"1. Slur / ...", "match":"병신", "start":10, "end":12}, ...]
        """
        if not text:
            return []
        self._maybe_reload()

        out: List[Dict[str, object]] = []
        with self._lock:
            for cat, rx in self._patterns.items():
                for m in rx.finditer(text):
                    tok = m.group(1)
                    s, e = m.span(1)
                    out.append({"category": cat, "match": tok, "start": s, "end": e})
        return out

    def is_blocked(self, text: str) -> bool:
        """매칭 결과가 하나라도 있으면 차단(True)으로 간주합니다."""
        return bool(self.scan(text))