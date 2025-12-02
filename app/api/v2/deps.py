from typing import Optional
from fastapi import Request, HTTPException
from app.callout.filter.xlmr_client import XLMRClient
from app.filters.v1.curse_detection_model import LocalCurseModel

from app.services.v1.recommender import Recommender as RecommenderV1
from app.services.v2.recommender import Recommender as RecommenderV2


from app.cluster.user_clustering import ClusteringTrainer
from app.cluster.gatherings_popularity import PopularityTrainer


def get_curse_model_dep(request: Request) -> LocalCurseModel:
    m = getattr(request.app.state, "curse_model", None)
    if m is None:
        raise HTTPException(status_code=500, detail="Curse model not initialized.")
    return m


def get_xlmr_client_dep(request: Request) -> Optional[XLMRClient]:
    return getattr(request.app.state, "xlmr_client", None)


# ------------------------------------------------------------------------------------------------


def get_recommender_v1(request: Request) -> RecommenderV1:
    """
    서버 기동 시 app.state.recommender에 올려둔 서비스를 꺼내서 주입합니다.
    없으면 500으로 실패시켜 원인을 바로 알 수 있게 합니다.
    """
    recommender = getattr(request.app.state, "recommender_v1", None)
    if recommender is None:
        raise HTTPException(status_code=500, detail="RecommenderV1 not initialized.")
    return recommender


def get_recommender_v2(request: Request) -> RecommenderV2:
    """
    서버 기동 시 app.state.recommender_v2에 올려둔
    RecommenderV2 인스턴스를 꺼내서 반환합니다.
    - 이 인스턴스는 내부에서 아티팩트(클러스터, 인기 방 테이블 등)를 캐싱하고,
    각 요청마다 같은 인스턴스를 재사용합니다.
    """
    recommender = getattr(request.app.state, "recommender_v2", None)
    if recommender is None:
        raise HTTPException(status_code=500, detail="RecommenderV2 not initialized.")
    return recommender


# ------------------------------------------------------------------------------------------------


def get_clustering_service_dep(request: Request) -> ClusteringTrainer:
    """
    서버 기동 시 app.state.clustering_service에 올려둔
    ClusteringService 인스턴스를 꺼내서 반환합니다.
    초기화가 안 되어 있으면 500 에러를 발생시켜 문제를 바로 알 수 있게 합니다.
    """
    clustering_service = getattr(request.app.state, "clustering_service", None)
    if clustering_service is None:
        raise HTTPException(status_code=500, detail="ClusteringService not initialized.")
    return clustering_service


def get_popularity_service_dep(request: Request) -> PopularityTrainer:
    """
    서버 기동 시 app.state.popularity_service에 올려둔
    PopularityService 인스턴스를 꺼내서 반환합니다.
    """
    popularity_service = getattr(request.app.state, "popularity_service", None)
    if popularity_service is None:
        raise HTTPException(status_code=500, detail="PopularityService not initialized.")
    return popularity_service
