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

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.schemas import (
    ClusterRefreshRequest,
    ClusterRefreshResponse,

    UserActionlog,
    PopularityRefreshRequest)


from app.cluster.user_clustering import ClusteringTrainer
from app.cluster.gatherings_popularity import PopularityTrainer

# ==========================
# 의존성 주입용 팩토리 함수
# ==========================
from app.api.v2.deps import (
    get_clustering_service_dep,
    get_popularity_service_dep,
)


router = APIRouter(
    prefix="/refresh",
    tags=["clustering_refresh"],
)


# http://127.0.0.1:8000/api/ai/v2/refresh/clustering
@router.post("/clustering", response_model=ClusterRefreshResponse)
def filter_check(
    req: ClusterRefreshRequest,
    service: ClusteringTrainer = Depends(get_clustering_service_dep)
) -> ClusterRefreshResponse:
    """
    [배치용 엔드포인트]

    - 백엔드가 DB에서 모든 사용자의 feature를 조회한 뒤,
        `ClusterRefreshRequest` 형식으로 AI 서버에 POST하는 시나리오를 가정합니다.
    - 이 엔드포인트는 다음과 같은 일을 수행합니다.
        1) 요청으로 받은 `users` 리스트를 기반으로 feature 전처리 (StandardScaler, SVD 등)
        2) K-means(또는 다른 군집 모델) 재학습
        3) 학습된 모델(scaler, svd, kmeans, vocab 등)을 아티팩트 파일로 저장
        4) 클러스터 품질 지표와 cluster별 사용자 수를 요약하여 응답으로 반환

    실제 구현 로직은 ClusteringService 내부에 두고,
    여기서는 서비스 메서드를 호출하는 역할만 담당합니다.
    """
    try:
        if not req.users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="사용자 리스트가 비어 있습니다. 최소 1명 이상의 사용자 정보가 필요합니다.",
            )

        result: ClusterRefreshResponse = service.refresh_clusters(req)
        return result

    except HTTPException:
        # 이미 위에서 HTTPException을 발생시킨 경우 그대로 전달합니다.
        raise

    except Exception as e:
        # 예기치 못한 예외는 500 에러로 래핑합니다.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"cluster refresh failed: {e}",
        )


# http://127.0.0.1:8000/api/ai/v2/refresh/popularity
@router.post("/popularity", status_code=204)    # 인기 방 테이블 재계산
def refresh_popularity(
    req: PopularityRefreshRequest,
    service: PopularityTrainer = Depends(get_popularity_service_dep)
) -> None:
    """
    [배치용 엔드포인트]

    - 백엔드가 UserActionCollection (user_id, room_id, status, created_at)을 기준으로
        일정 기간(예: 최근 30일)의 행동 로그를 `PopularityRefreshRequest` 형식으로 모아
        AI 서버에 POST하는 시나리오입니다.

        - 이 엔드포인트가 하는 일:
        1) log_list 각 row에 대해 user_id → cluster_id를 붙임
            (cluster_id가 백엔드 DB에 있으면 붙여서 보낼 수도 있고,
            AI 서버가 user_id → cluster_id 매핑을 내부적으로 가지고 있을 수도 있습니다.)
        2) (cluster_id, room_id, status, created_at)을 이용해
            군집별 popularity score를 계산
            예: 참여=1.0, 클릭=0.3, 시간 감쇠 e^{-λ * days_since_join} 적용
        3) 계산된 결과를 `cluster_room_popularity` 아티팩트 파일로 저장
            (나중에 RecommenderV2가 실시간 추천 시 이 파일을 로드해서 사용합니다.)

        - 반환 바디는 없고, 성공 시 HTTP 204 응답만 보냅니다.
        (배치 스케줄러 입장에서는 '성공/실패'만 확인하면 되기 때문에 이렇게 설계했습니다.)
    """
    try:
        # log_list가 비어 있는 경우, 단순히 아무 것도 하지 않고 성공으로 처리할지
        # 400 에러로 처리할지는 정책에 따라 결정하시면 됩니다.
        # 여기서는 "비어 있으면 할 일이 없다"라고 보고 조용히 반환하는 쪽으로 가정하겠습니다.
        if not req.log_list:
            return

        service.refresh_popularity(req)
        # 반환값이 없으므로, FastAPI가 자동으로 204 No Content를 응답합니다.

    except Exception as e:
        # 예기치 못한 예외는 500 에러로 래핑합니다.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"popularity refresh failed: {e}",
        )
