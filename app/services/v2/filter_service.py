# app/services/v2/filter.py
# 역할:
#   - 텍스트 필터링 비즈니스 로직을 담당합니다.
#   - 파이프라인: 전처리(normalize) → 블랙리스트 매칭 → 정책 라우팅 → 모델 추론 → 판정
#
# 의존관계:
#   - app/processors/filter_preprocessing.py  : TextPreprocessor, LengthBasedRouter
#   - app/filters/v1/blocklistV0.py           : BlacklistMatcher
#   - app/filters/v1/curse_detection_model.py : LocalCurseModel
#   - app/callout/filter/xlmr_client.py       : XLMRClient (Optional)
#   - app/processors/filter_postprocessing.py : FilterDecision, to_filter_check_response

from __future__ import annotations
import asyncio
import logging
from typing import Optional

from app.processors.filter_preprocessing import (
    TextPreprocessor,
    PreprocessConfig,
    LengthBasedRouter,
)

from app.filters.v1.blocklistV0 import BlacklistMatcher
from app.filters.v1.curse_detection_model import LocalCurseModel
from app.callout.filter.xlmr_client import XLMRClient

from app.processors.filter_postprocessing import FilterDecision, to_filter_check_response

from app.models.schemas import FilterCheckResponse


logger = logging.getLogger(__name__)


class FilterService:
    """
    텍스트 필터링 서비스.

    엔드포인트에서 curse, xlmr 의존성을 주입받아 생성합니다.

    사용 예:
        service = FilterService(curse=curse_model, xlmr=xlmr_client)
        response = service.check("검사할 텍스트")
    """

    _preprocessor = TextPreprocessor(PreprocessConfig())
    _router = LengthBasedRouter()
    _matcher = BlacklistMatcher(hot_reload=True)

    def __init__(
        self,
        curse: LocalCurseModel,
        xlmr: Optional[XLMRClient] = None,
    ) -> None:
        self._curse = curse
        self._xlmr = xlmr

    def check(self, text: str) -> FilterCheckResponse:
        """
        필터 파이프라인 실행 후 FilterCheckResponse 반환.

        1) 전처리: 의미 변경 없이 표준화
        2) 블랙리스트: 명시 단어 매칭 시 즉시 차단
        3) 정책 라우팅: 텍스트 길이 기반으로 curse / xlmr 선택
        4) 모델 추론: 라우팅 결과에 따라 모델 호출 (xlmr 없으면 curse fallback)
        5) 임계값 비교 후 판정
        """
        # 1) 전처리
        normalized = self._preprocessor.preprocess(text)

        # 2) 블랙리스트
        bl_hits = self._matcher.scan(normalized)
        if bl_hits:
            decision = FilterDecision(
                allowed=False,
                score=1.0,
                route="blacklist_block",
                threshold=None,
                blacklist=bl_hits,
            )
            return to_filter_check_response(decision)

        # 3) 정책 라우팅
        policy = self._router.policy(normalized)

        # 4) 모델 추론
        if policy.route == "xlmr":
            ml_score = (
                self._xlmr.predict(normalized)
                if self._xlmr is not None
                else self._curse.predict(normalized)  # xlmr 없으면 curse fallback
            )
        else:
            ml_score = self._curse.predict(normalized)

        # 5) 판정
        decision = FilterDecision(
            allowed=ml_score < policy.threshold,
            score=ml_score,
            route=policy.route,
            threshold=policy.threshold,
            blacklist=[],
        )

        logger.warning(
            "fitler → fallback(2): route=%s score=%s allowed=%s",
            decision.route,
            decision.score,
            decision.allowed
        )

        return to_filter_check_response(decision)

    async def check_async(self, text: str) -> FilterCheckResponse:
        """
        비동기 필터 파이프라인.
        - 전처리/블랙리스트: 가볍기 때문에 그대로 동기 호출
        - xlmr: 외부 API 호출 → await predict_async
        - curse: CPU 연산 → run_in_executor로 이벤트루프 분리
        """
        # 1) 전처리 — 가벼운 문자열 연산, executor 불필요
        normalized = self._preprocessor.preprocess(text)

        # 2) 블랙리스트 — 정규식 매칭, 마찬가지로 가벼움
        bl_hits = self._matcher.scan(normalized)
        if bl_hits:
            decision = FilterDecision(
                allowed=False,
                score=1.0,
                route="blacklist_block",
                threshold=None,
                blacklist=bl_hits,
            )
            return to_filter_check_response(decision)

        # 3) 정책 라우팅
        policy = self._router.policy(normalized)

        # 4) 모델 추론
        loop = asyncio.get_event_loop()

        ml_score = None
        actual_route = policy.route  # 실제로 탄 경로 추적

        if policy.route == "xlmr" and self._xlmr is not None:
            ml_score = await self._xlmr.predict_async(normalized)

        if ml_score is None:  # fallback
            ml_score = await loop.run_in_executor(None, self._curse.predict, normalized)
            actual_route = "curse"

        # 5) 판정
        decision = FilterDecision(
            allowed=ml_score < policy.threshold,
            score=ml_score,
            route=actual_route,
            threshold=policy.threshold,
            blacklist=[],
        )

        logger.warning(
            "filter → route=%s score=%s allowed=%s",
            decision.route,
            decision.score,
            decision.allowed,
        )

        return to_filter_check_response(decision)
