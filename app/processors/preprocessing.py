'''
	•	역할: 카테고리 문자열 정규화(소문자화, 공백 트림, 동의어 매핑 등).
	•	현재는 뼈대만 제공합니다. 추후 정책 확정 시 내부를 채우세요.

'''

# app/processors/preprocessors.py
# 역할:
# - 입력 텍스트/카테고리의 표준화를 담당합니다.
# - 본 파일은 선택 사항이며, 나중에 동의어/표기 통일 정책이 정해지면 확장.
# - 본 파일은 카테고리가 텍스트 형태로 넘어온다고 생각하며, 다시 논의 후 카테고리를 어떻게 넘길 지 확실하게 정의해야함.

from typing import Optional

SYNONYM_MAP = {
    # 예: "스터디": ["공부", "study"],
    #     "운동": ["피트니스", "헬스"],
}

def normalize_category(cat: Optional[str]) -> Optional[str]:
    """
    카테고리 문자열을 표준 형태로 변환합니다.
    - 소문자화/공백 정리/동의어 매핑 등을 수행합니다.
    """
    if not cat:
        return cat
    c = cat.strip()
    # 필요 시 소문자화: c = c.lower()
    # 동의어 매핑: 역매핑 테이블을 만들어 "공부" -> "스터디" 등으로 통일
    return c