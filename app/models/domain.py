# app/models/domain.py
# 역할: 내부 도메인/계산에 최적화된 경량 구조체(dataclass 등)를 정의,
#      검증 오버헤드가 적고, 서비스 계층에서 대량 계산에서 사용.
# 사용처: app/services/* (비즈니스 로직), 레포지토리 계층

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class RoomRecommandUserMeta:
    """
    추천 시 필요한 사용자 신호만 담는 내부용 DTO.
    - 외부 요청과 1:1이 아니며, 엔드포인트에서 가공해 만듭니다.
    """

    '''
    user_id -> 사용자들을 구별하기 위함.
    preferred_categories -> 사용자의 선호 카테고리를 확인 및 비교를 위함
    class_user -> 학번이 비슷한 인원들이 있는 방을 추천하기 위함.
    '''
    user_id: int
    preferred_categories: list[str]
    student_year: int


@dataclass
class RoomRecommandRoomMeta:
    """
    추천 점수 계산을 위한 최소 필드만 담는 내부용 DTO.
    - DB/ORM 전체 모델과 1:1이 아닙니다(가벼움이 목적).
    """

    '''
    room_id -> 방들의 구별
    category -> category 확인 및 비교를 위함

    capacity_member -> 멤버의 정원
    current_member -> 현재 멤버 count
    updated_at -> 콜드스타트에서 최신순을 정렬하기 위함.
    '''
    room_id: int
    category: str
    member_list: list[RoomRecommandUserMeta]

    # 콜드스타트 경로에서만 사용
    capacity_member: int
    current_member: int
    updated_at: Optional[datetime]


@dataclass
class TextFilter:
    """
    모임 소개문 자동생성의 최소 필드만 담는 내부용 DTO.
    - DB/ORM 전체 모델과 1:1이 아닙니다(가벼움이 목적).
    """
    '''
    - request_id: string (선택) — 클라이언트 생성 추적 ID
    - user_id: long (선택) — 지속적인 금칙어, 비속어 사용시 제재를 위함.
    - scenario: enum(string) [nickname | room_intro | review | free_text] (필수)
    - text: string (필수) — 검사 대상 원문
    - use_ml: boolean (default : false in MVP) — HF 모델 사용 여부
    '''
    request_id: str
    user_id: str
    scenario: str
    text: str
    gender_neutral: bool = True


@dataclass
class AutoWrite:
    """
    모임 소개문 자동생성의 최소 필드만 담는 내부용 DTO.
    - DB/ORM 전체 모델과 1:1이 아닙니다(가벼움이 목적).
    """

    '''
    - room_id: Long -> 방들의 구별
    - title: str -> 방 제목또한 소개문에 기입
    - keywords: list[str] -> 사용자가 자동소개를 원할 때 넘길 키워드들
    - category: str -> 카테고리를 중심으로 서술
    - location: str -> 어느 곳을 중심으로 모일 것인지
    - data_time: str -> 언제 만날 지
    - max_participants: int -> 모임의 정원
    - gender_neutral: Boolean - 성중립 표현 true로 고정
    - max_chars: int - 생성 글자 수 제한 (500자 ~ 800자)
    '''
    room_id: int
    title: str
    keywords: list[str]
    category: str
    location: str
    data_time: str
    max_participants: int
    gender_neutral: bool = True
    max_chars: int = 800
