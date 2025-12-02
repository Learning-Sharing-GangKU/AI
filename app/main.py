# app/main.py
# 역할:
# - FastAPI 앱 엔트리포인트
# - 서버 기동 시 HuggingFace 모델을 한 번 다운로드(snapshot_download)
#   → 이후부터는 캐시에서 사용 (오프라인 모드 가능)
# - 워밍업: 간단한 텍스트로 모델을 1회 호출하여 로딩 지연을 앱 시작 시 해결

from fastapi import FastAPI
# from app.api.v1.router import api_v1_router
from app.api.v2.router import api_v2_router
from huggingface_hub import snapshot_download
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, RequestResponseLoggerMiddleware

# 서비스/클라이언트
from app.filters.v1.curse_detection_model import LocalCurseModel
from app.callout.filter.registry import init_xlmr_client, get_xlmr_client
from app.services.v1.recommender import Recommender as RecommenderV1, CategoryIndex
from app.services.v2.recommender import Recommender as RecommenderV2
from app.cluster.user_clustering import ClusteringTrainer
from app.cluster.gatherings_popularity import PopularityTrainer

app = FastAPI(title="gangKU AI Server")
app.include_router(api_v2_router, prefix="/api")



def _init_logging(app: FastAPI) -> None:
    setup_logging("INFO")
    app.add_middleware(RequestResponseLoggerMiddleware)


def _init_cors(app: FastAPI) -> None:
    # 반드시 origins 지정 (없으면 CORS 차단)
    origins = getattr(settings, "CORS_ALLOW_ORIGINS", ["*"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _init_routes(app: FastAPI) -> None:
    # v2 모두 마운트
    app.include_router(api_v2_router, prefix="/api")  # 기존대로 유지 (원하면 "/api/v2"로 변경)


def _init_hf_cache() -> None:
    # 1. 모델 파일 캐시 다운로드 (없으면 받음, 있으면 캐시 활용)
    try:
        snapshot_download(
            repo_id=settings.CURSE_MODEL_ID,
            token=None,
            local_files_only=False,
        )
        print("[Startup] HF snapshot_download ok.")
    except Exception as e:
        print(f"[Startup] HF snapshot_download skipped/failed: {e}")


def _init_curse_model(app: FastAPI) -> None:
    # 2. 욕설 이진 모델 로드 & 워밍업
    try:
        model = LocalCurseModel()
        _ = model.predict("안녕하세요")  # 워밍업
        app.state.curse_model = model
        print("[Startup] Curse model warmed up.")
    except Exception as e:
        app.state.curse_model = None
        print(f"[Startup] Curse model init/warmup failed: {e}")


def _init_xlmr(app: FastAPI) -> None:
    # --------------------xlmr load--------------------
    # 1. XLMR 클라이언트 준비(환경변수 필요: XLMR_BASE_URL, XLMR_PATH, (선택)XLMR_API_KEY)
    try:
        init_xlmr_client()
        xlmr = get_xlmr_client()
        app.state.xlmr_client = xlmr
        if xlmr is None:
            print("[Startup] XLMR client not configured (env missing).")
        else:
            try:
                _ = xlmr.predict("this is a normal sentence")  # 네트워크 상황 따라 실패 가능
                print("[Startup] XLMR client warmed up.")
            except Exception:
                print("[Startup] XLMR warmup failed (network). Will fallback until reachable.")
    except Exception as e:
        app.state.xlmr_client = None
        print(f"[Startup] XLMR init/warmup failed: {e}")


def _init_recommenders(app: FastAPI) -> None:
    # --- Recommender (deps.get_recommender 가 요구, v1, v2 둘 다 올리기) ---
    try:
        app.state.recommender_v1 = RecommenderV1(cat_index=CategoryIndex())
        print("[Startup] Recommender v1 ready.")
    except Exception as e:
        app.state.recommender_v1 = None
        print(f"[Startup] Recommender v1 init failed: {e}")

    try:
        app.state.recommender_v2 = RecommenderV2(artifacts_dir=settings.CLUSTER_ARTIFACT_DIR)
        print("[Startup] Recommender v2 ready.")
    except Exception as e:
        app.state.recommender_v2 = None
        print(f"[Startup] Recommender v2 init failed: {e}")


def _init_batch_services(app: FastAPI) -> None:
    # --- Clustering / Popularity batch services ---
    try:
        app.state.clustering_service = ClusteringTrainer(artifacts_dir=settings.CLUSTER_ARTIFACT_DIR)
        app.state.popularity_service = PopularityTrainer(artifacts_dir=settings.POPULARITY_ARTIFACT_DIR)
        print("[Startup] Clustering / Popularity services ready.")
    except Exception as e:
        app.state.clustering_service = None
        app.state.popularity_service = None
        print(f"[Startup] Clustering / Popularity services init failed: {e}")


def create_app() -> FastAPI:
    app = FastAPI(title="gangKU AI Server")
    _init_logging(app)
    _init_cors(app)
    _init_routes(app)

    @app.on_event("startup")
    def startup_event() -> None:
        """
        서버 시작 시 실행되는 훅(hook).
        - 모델 파일을 캐시에 다운로드 (최초 1회만 네트워크 필요)
        """
        _init_hf_cache()
        _init_curse_model(app)
        _init_xlmr(app)
        _init_recommenders(app)
        _init_batch_services(app)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()
