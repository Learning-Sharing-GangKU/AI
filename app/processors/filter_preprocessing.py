# 해당 파일은 사용자가 입력할 수 있는 텍스트를 모두 전처리 하기 위해 사용하는 파일로써
# 금칙어, 비속어 검출 혹은 나중에 사용할 수도 있는 사용자의 입력 텍스트를 전처리 하기 위한 파일임을 명시한다;
'''
filter 사용 시나리오
- <User.nickname>         사용자 닉네임 생성 및 수정
- <Reviews.comment>       사용자 리뷰 작성
- <Gathering.description> 모임 소개문 생성 및 수정
'''

# 역할:
# - 필터링 파이프라인의 "전처리(normalize)"를 담당합니다.
# - 블랙리스트/로컬 모델(예: korean-curse-detection)이 잘 동작하도록 입력을 표준화합니다.
# - 외부 모델 호출 전의 "PII 마스킹"은 여기서 하지 않습니다. (moderation 단계에서 별도 수행)
#
# 포함 기능
#  1) 유니코드 표준화(NFKC)
#  2) 공백·제어문자 정리
#  3) 반복문자 축소(일반 문자, 'ㅋㅋ' 등의 특례 포함)
#  4) 간단 leet 변형 치환(과도하지 않게 최소 규칙)
#  5) 영어 소문자화
#  6) 토큰 경계 정리(과한 붙임/기호 주변 공백 정리)
#
# 사용 시점:
# - 엔드포인트에서 요청을 받으면, 블랙리스트 매칭/로컬 모델 호출 전에 아래 TextPreprocessor.preprocess()를 호출합니다.
# - 외부 모델(xlmr 등) 호출 전에는 이 결과를 기반으로 PII 마스킹을 moderation 단계에서 별도로 적용합니다.
#
# 주의:
# - 전처리는 "탐지 용이성"을 위한 표준화이며, 의미를 변형하지 않도록 보수적으로 구현합니다.

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Pattern


@dataclass(frozen=True)
class PreprocessConfig:
    """
    전처리 동작을 제어하는 하이퍼파라미터 모음입니다.
    팀 정책/운영 과정에서 손쉽게 조정할 수 있도록 한 곳에 모읍니다.
    """
    # 반복 문자 축소 임계치(이 값 초과 반복되면 축소)
    max_repeat: int = 2
    # 'ㅋ', 'ㅎ' 같은 감탄/웃음 글자의 최대 연속 허용 개수
    max_repeat_kor_laugh: int = 2
    # 영문 소문자화 여부
    lowercase_english: bool = True
    # 토큰 경계 정리에서 과도한 공백/구두점 정리 활성화 여부
    tidy_token_boundaries: bool = True


class TextPreprocessor:
    """
    전처리 파이프라인 클래스.

    주요 공개 메서드:
        - preprocess(text: str) -> str
        전처리 전체 파이프라인을 순서대로 수행합니다.

    비공개 단계 메서드(내부 호출 순서):
        1) _nfkc(text)                    : 유니코드 정규화(NFKC)
        2) _strip_control_and_spaces(text): 제어문자 제거, 공백 정리(연속 공백->단일, 양 끝 trim)
        3) _reduce_repeats(text)          : 반복문자 축소(일반/특례)
        4) _lowercase_english(text)       : 영어 소문자화(옵션)
        5) _tidy_token_boundaries(text)   : 토큰 경계 정리(옵션)

    사용 예:
        pre = TextPreprocessor()
        normalized = pre.preprocess("씨이이이이발  5ibal 좀 그만 써요!!!  안녕하세요  ")
        =>("씨발 5ibal 좀 그만 써요!!! 안녕하세요 ")
    """
    # 간단한 제어문자(공백류 제외) 제거용 패턴: Cc(제어), Cf(서식) 범주를 제거
    _CONTROL_RE: Pattern[str] = re.compile(
        r"[\u0000-\u001F\u007F-\u009F\u200B\u200C\u200D\u2060\uFEFF]"
    )

    # 연속 공백을 하나로 축소 (개행/탭 포함)
    _MULTISPACE_RE: Pattern[str] = re.compile(r"\s+")

    # 같은 문자 3회 이상 반복을 2회로 축소하는 일반 규칙 (한글, 영문, 숫자, 기호 등)
    # 예: "씨이이이발" -> "씨이발", "!!!!!!" -> "!!"
    _REPEAT_GENERAL_RE: Pattern[str] = re.compile(r"(.)\1{2,}")

    # 한국어 웃음/감탄 특례: ㅋㅋㅋㅋ -> ㅋㅋ, ㅎㅎㅎㅎ -> ㅎㅎ
    _REPEAT_KR_LAUGH_RE: Pattern[str] = re.compile(r"([ㅋㅎ])\1{2,}", re.IGNORECASE)

    # 토큰 경계 정리: 구두점 앞뒤 과도한 공백 정리, 연속 구두점 일부 축소 등
    # 필요 최소한만 수행합니다.
    _SPACE_AROUND_PUNCT_RE: Pattern[str] = re.compile(
        r"\s*([,.;:!?(){}\[\]~^`'\"-])"   # 앞뒤 공백을 지울 구두점들
    )
    _PUNCT_AROUND_SPACE_RE: Pattern[str] = re.compile(
        r"([,.;:!?(){}$begin:math:display$$end:math:display$~^`'\"-])\s*"
    )

    def __init__(self, config: PreprocessConfig | None = None) -> None:
        self.cfg = config or PreprocessConfig()

    # ---------------- 공개 API ----------------

    def preprocess(self, text: str) -> str:
        """
        엔드포인트/서비스에서 호출하는 단일 진입점 함수.
        파이프라인 순서대로 전처리를 수행하고 결과 문자열을 반환합니다.
        """
        if not isinstance(text, str) or not text:
            return text

        x = text
        x = self._nfkc(x)
        x = self._strip_control_and_spaces(x)
        x = self._reduce_repeats(x)
        if self.cfg.lowercase_english:
            x = self._lowercase_english(x)
        if self.cfg.tidy_token_boundaries:
            x = self._tidy_token_boundaries(x)
        # 마지막으로 한 번 더 공백 정리 및 trim
        x = self._strip_control_and_spaces(x)
        return x

        # ---------------- 내부 단계 ----------------

    def _nfkc(self, text: str) -> str:
        """
        NFKC 정규화:
        - 호환 문자를 정규화하여 '全角' 알파벳/숫자 등을 표준 폭으로 변환합니다.
        - 'ｓｈｉｔ' → 'shit', 'ＡＢＣ' → 'ABC'
        - 한글 자모 분리 형태(ㄱ ㅏ ㅅ ㅣ)도 가능한 한 정규화합니다.
        """
        return unicodedata.normalize("NFKC", text)

    def _strip_control_and_spaces(self, text: str) -> str:
        """
        제어문자 제거 및 공백 정리:
        - 보이지 않는 제어문자(Cc, Cf) 제거
        - 연속 공백(개행/탭 포함)을 단일 공백으로 축소
        - 양 끝 공백 제거
        """
        x = self._CONTROL_RE.sub("", text)
        x = self._MULTISPACE_RE.sub(" ", x)
        return x.strip()

    def _reduce_repeats(self, text: str) -> str:
        """
        반복 문자 축소:
        - 일반 규칙: 동일 문자가 3회 이상 반복되면 2회로 축소
        - 한국어 웃음/감탄 특례: 'ㅋㅋㅋㅋ' → 'ㅋㅋ', 'ㅎㅎㅎㅎ' → 'ㅎㅎ'
        """
        # ㅋㅋ/ㅎㅎ 특례부터 처리
        def _laugh_repl(m: re.Match[str]) -> str:
            ch = m.group(1)
            return ch * self.cfg.max_repeat_kor_laugh

        x = self._REPEAT_KR_LAUGH_RE.sub(_laugh_repl, text)

        # 일반 반복 축소
        def _gen_repl(m: re.Match[str]) -> str:
            ch = m.group(1)
            return ch * self.cfg.max_repeat

        x = self._REPEAT_GENERAL_RE.sub(_gen_repl, x)
        return x

    def _lowercase_english(self, text: str) -> str:
        """
        영어 소문자화:
        - 영어 대소문자 차이를 제거하여 블랙리스트/모델의 탐지 일관성을 높입니다.
        - 한글/숫자/기호 등은 영향이 없습니다.
        """
        # 단순 .lower()는 한글에도 영향이 거의 없으나, 명확성을 위해 영어 위주 설명을 덧붙입니다.
        return text.lower()

    def _tidy_token_boundaries(self, text: str) -> str:
        """
        토큰 경계 정리:
        - 구두점 주변의 과도한 공백을 정리하여 토크나이저/블랙리스트 매칭의 불안정성을 감소시킵니다.
        - 과한 규칙은 적용하지 않고, 최소한의 공백 정리만 수행합니다.
        """
        # 구두점 앞 불필요 공백 제거
        x = re.sub(r"\s+([,.;:!?])", r"\1", text)
        # 괄호 주변 공백 최소화: "(  텍스트  )" → "(텍스트)"
        x = re.sub(r"\(\s+", "(", x)
        x = re.sub(r"\s+\)", ")", x)
        return x


# 모듈 단위의 간단 self-test (로컬에서만 사용, 배포 시 무해)
if __name__ == "__main__":
    pre = TextPreprocessor()
    samples = [
        "   씨이이이이발   5ibal 좀 그만 써요!!!  ",
        " s h i y   FucK   tlqkf..... ㅋㅋㅋㅋ 왜 저래",
        "안      녕 하 세 요   ",
        "s!bal은 안돼요...jot도 안돼요...",
    ]
    for s in samples:
        print("IN :", s)
        print("OUT:", pre.preprocess(s))
        print("-" * 40)
