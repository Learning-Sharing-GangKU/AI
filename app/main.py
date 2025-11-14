# app/main.py
# 역할:
# - FastAPI 앱 엔트리포인트
# - 서버 기동 시 HuggingFace 모델을 한 번 다운로드(snapshot_download)
#   → 이후부터는 캐시에서 사용 (오프라인 모드 가능)
# - 워밍업: 간단한 텍스트로 모델을 1회 호출하여 로딩 지연을 앱 시작 시 해결

from fastapi import FastAPI
from app.api.v1.router import api_v1_router
from huggingface_hub import snapshot_download
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, RequestResponseLoggerMiddleware


app = FastAPI(title="gangKU AI Server")
app.include_router(api_v1_router, prefix="/api/v1")

setup_logging("INFO")
app.add_middleware(RequestResponseLoggerMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """
    서버 시작 시 실행되는 훅(hook).
    - 모델 파일을 캐시에 다운로드 (최초 1회만 네트워크 필요)
    - LocalCurseModel을 전역으로 로드
    - 간단한 워밍업 호출 실행
    """
    # --------------------curse detection load--------------------
    # 1. 모델 파일 캐시 다운로드 (없으면 받음, 있으면 캐시 활용)
    try:
        snapshot_download(
            repo_id=settings.CURSE_MODEL_ID,
            token=None,                 # 공개 모델이므로 명시적으로 None
            local_files_only=False      # 캐시에 없으면 받음
        )
        print("[Startup] HF snapshot_download ok.")
    except Exception as e:
        print(f"[Startup] HF snapshot_download skipped/failed: {e}")

    # 2. 욕설 이진 모델 로드 & 워밍업
    try:
        from app.filters.v1.curse_detection_model import LocalCurseModel
        _CURSE_MODEL = LocalCurseModel()  # model_id가 None이면 settings에서 읽음
        app.state.curse_model = _CURSE_MODEL
        _ = _CURSE_MODEL.predict("안녕하세요")
        print("[Startup] Curse model warmed up.")
        # ★ 엔드포인트에서 접근할 수 있도록 app.state에 저장
        app.state.curse_model = _CURSE_MODEL
    except Exception as e:
        print(f"[Startup] Curse model init/warmup failed: {e}")

    # --------------------xlmr load--------------------
    # 1. XLMR 클라이언트 준비(환경변수 필요: XLMR_BASE_URL, XLMR_PATH, (선택)XLMR_API_KEY)
    try:
        from app.callout.filter.registry import init_xlmr_client, get_xlmr_client
        init_xlmr_client()  # env 기반 초기화
        xlmr = get_xlmr_client()
        app.state.xlmr_client = xlmr

        if xlmr is None:
            print("[Startup] XLMR client not configured (env missing).")
        else:
            # 3-1) 워밍업
            _ = xlmr.predict("this is a normal sentence")
            print(_)

            if _ != 0:
                print("[Startup] XLMR client warmed up.")
            else:
                print("[Startup] XLMR warmup failed (network). Will fallback until reachable.")

    except Exception as e:
        # 외부 모델 장애가 있어도 서버 부트는 계속할지 여부는 정책으로 결정
        print(f"[Startup] XLMR init/warmup failed: {e}")

        # --- Recommender (deps.get_recommender 가 요구) ---
    try:
        from app.services.v1.recommender import Recommender, CategoryIndex
        # 필요한 의존이 더 있으면 아래에서 채워 넣기
        app.state.recommender = Recommender(cat_index=CategoryIndex())
        print("[Startup] Recommender ready.")
    except Exception as e:
        print(f"[Startup] Recommender init failed: {e}")


@app.get("/health")
def health_check():
    """
    서버 헬스체크 엔드포인트
    """
    return {"status": "ok"}
