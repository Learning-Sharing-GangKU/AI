from functools import lru_cache
from app.services.v1.recommender import Recommender, CategoryIndex
# from app.repositories.rooms import RoomRepository

CATEGORY_VOCAB = ["스터디", "운동", "독서", "게임", "음악", "봉사", "여행"]


@lru_cache
def get_cat_index() -> CategoryIndex:
    return CategoryIndex(CATEGORY_VOCAB)


# @lru_cache
# def get_room_repo() -> RoomRepository:
#     return RoomRepository()


@lru_cache
def get_recommender() -> Recommender:
    return Recommender(cat_index=get_cat_index())
