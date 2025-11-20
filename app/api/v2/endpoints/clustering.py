# app/api/v2/endpoints/recommendations.py
# 역할:
# - 주기적으로 유저 클러스터를 최신화 하기 위함.
# - 백엔드에서, user들 리스트를 request로 넘겨준다.

#  user feature
# - 나이
#     - 수치형
#     - StandardScaler
# - 학번
#     - 수치형
#     - StandardScaler
# - 참가 횟수 → 백이 DB에서 사용자 아이디 기반으로 count query 수행
#     - 수치형
#     - StandardScaler
# - SVD dense vector
#     - 선호 카테고리 1
#     - 선호 카테고리 2
#     - 선호 카테고리 3
# 선호 카테고리 1-3을 multi-hot vector로 표현
# → 해당 vector dense로 다시 나타냄 (**Truncated SVD 사용**)


from fastapi import APIRouter, HTTPException, Depends

from app.models.schemas import (
    ClusterRefreshRequest,
    ClusterRefreshResult)

router = APIRouter(
    prefix="/clustering",
    tags=["clustering_refresh"],
)


@router.post("/refresh", response_model=ClusterRefreshResult)
def filter_check(
    req: ClusterRefreshRequest,
    # 나중에 모델 만들면 setting으로 get_recommeder_model 이런 식으로 해줘야됨
) -> ClusterRefreshResult:
    print("hello")
