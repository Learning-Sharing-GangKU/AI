# app/filters/v1/curse_model.py
# 역할:
# - "2tle/korean-curse-detection" 모델을 로컬에서 로드하여,
#   입력 텍스트가 "욕설일 확률"을 반환
# - 본 클래스는 엔드포인트에서 직접 호출되거나,
#   이후 또 다른 외부 모델과 assemble로 사용될 수 있다,

from typing import List, Dict, Any
# import os
import torch
from transformers import pipeline


def _select_device() -> int:
    """
    장치 선택:
    - MPS(Apple Silicon)가 가능하면 device=0
    - 아니면 CPU로 device=-1
    """
    try:
        if torch.backends.mps.is_available() and torch.backends.mps.is_built():
            return 0  # pipeline에선 mps=0 인덱스로 취급
    except Exception:
        pass
    return -1  # CPU


class LocalCurseModel:
    """
    사용 방법:
        model = LocalCurseModel()          # 앱 시작 시 1회 생성(싱글턴처럼 운용 권장)
        prob = model.score("문자열 입력")   # '욕설일 확률' float(0~1)을 반환
    동작 개요:
        - pipeline(return_all_scores=True)로 로드 → LABEL_0/LABEL_1 확률 모두 획득
        - LABEL_1(또는 '1')을 '욕설 확률'로 간주하여 반환
    """
    def __init__(self, model_id: str = "2tle/korean-curse-detection") -> None:
        self.model_id = model_id
        device = _select_device()

        # return_all_scores=True로 꼭 설정해야 두 라벨 모두의 확률을 얻을 수 있습니다.
        self.pipe = pipeline(
            "text-classification",
            model=self.model_id,
            tokenizer=self.model_id,
            return_all_scores=True,
            truncation=True,
            device=device
        )

    def score(self, text: str) -> float:
        """
        입력 텍스트 1건에 대해 '욕설일 확률'을 반환합니다.
        - 출력 예시(파이프라인 결과):
            [[{'label':'LABEL_0','score':0.012}, {'label':'LABEL_1','score':0.988}]]
        - 여기서 LABEL_1(또는 '1')의 score를 곧바로 반환합니다.
        """
        if not text:
            return 0.0

        outputs: List[List[Dict[str, Any]]] = self.pipe(text)
        if not outputs or not outputs[0]:
            return 0.0

        row = outputs[0]
        # 라벨 표기 방어: 'LABEL_1' 또는 '1' 모두 대응
        scores = {str(d["label"]).upper(): float(d["score"]) for d in row}
        return scores.get("LABEL_1", scores.get("1", 0.0))
