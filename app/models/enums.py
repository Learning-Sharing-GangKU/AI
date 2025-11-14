from enum import StrEnum, unique


@unique
class Category(StrEnum):
    """
    방의 단일 카테고리. -> 추후 더 추가.
    """
    STUDY = "공부"
    SPORTS = "은동"
    BOOK = "독서"
    MUSIC = "음악"
    GAME = "게임"

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
