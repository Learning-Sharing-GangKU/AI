from enum import StrEnum, unique


@unique
class Category(StrEnum):
    """
    방의 단일 카테고리. -> 추후 더 추가.
    """

    SPORTS = "스포츠"
    FRIEND = "친목"
    BOOK = "독서"
    TRAVEL = "여행"
    MUSIC = "음악"
    STUDY = "스터디"
    GAME = "게임"
    FESTIVAL = "공연/축제"
    VOLUNTEER = "봉사활동"
    PHOTO = "사진"
    PET = "반려동물"
    EXERCISE = "운동"
    COOK = "요리"

    def _cat_name(x) -> str:
        if x is None:
            return ""
        return x.value if isinstance(x, Category) else str(x)


@unique
class Scenario(StrEnum):
    """
    금칙어/비속어 필터에서 사용하는 시나리오 구분.
    """
    NICKNAME = "nickname"
    KEYWORD = "keyword"
    REVIEW = "review"
    GATHERING = "gathering"
    TITLE = "title"


@unique
class UserStatus(StrEnum):
    """
    백에서 로그 받아 올 때, 해당 로그가 참여를 해서 생성된 로그인지, 클릭을 해서 생성된 로그인지
    """
    JOIN = "join"
    CLICK = "click"
