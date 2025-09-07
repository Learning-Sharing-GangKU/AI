# app/models/domain.py
# 역할: 내부 도메인/계산에 최적화된 경량 구조체(dataclass 등)를 정의,
#      검증 오버헤드가 적고, 서비스 계층에서 대량 계산에서 사용.
# 사용처: app/services/* (비즈니스 로직), 레포지토리 계층

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class RoomMeta:
    """
    추천 점수 계산을 위한 최소 필드만 담는 내부용 DTO.
    - DB/ORM 전체 모델과 1:1이 아닙니다(가벼움이 목적).
    """
    room_id: int
    title: str
    category: str
    region: Optional[str]
    member_count: int
    updated_at: Optional[datetime]   # 콜드스타트 경로에서만 사용

@dataclass
class UserProfile:
    """
    추천 시 필요한 사용자 신호만 담는 내부용 DTO.
    - 외부 요청과 1:1이 아니며, 엔드포인트에서 가공해 만듭니다.
    """
    user_id: int
    preferred_categories: list[str]
    class_user: int