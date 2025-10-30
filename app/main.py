# app/main.py
# 역할:
# - FastAPI 앱 엔트리포인트
# - 서버 기동 시 HuggingFace 모델을 한 번 다운로드(snapshot_download)
#   → 이후부터는 캐시에서 사용 (오프라인 모드 가능)
# - 워밍업: 간단한 텍스트로 모델을 1회 호출하여 로딩 지연을 앱 시작 시 해결

from fastapi import FastAPI
from huggingface_hub import snapshot_download
from app.filters.v1.curse_detection_model import LocalCurseModel

app = FastAPI(title="gangKU AI Server")

# 전역 싱글턴(한 번만 로드)
_CURSE_MODEL: LocalCurseModel | None = None


@app.on_event("startup")
def startup_event():
    """
    서버 시작 시 실행되는 훅(hook).
    - 모델 파일을 캐시에 다운로드 (최초 1회만 네트워크 필요)
    - LocalCurseModel을 전역으로 로드
    - 간단한 워밍업 호출 실행
    """
    global _CURSE_MODEL

    # 1. 모델 파일 캐시 다운로드 (없으면 받음, 있으면 캐시 활용)
    snapshot_download(repo_id="2tle/korean-curse-detection")

    # 2. 모델 로드
    _CURSE_MODEL = LocalCurseModel()

    # 3. 워밍업 호출 (첫 요청 시 지연 방지)
    try:
        _ = _CURSE_MODEL.score("안녕하세요")
        print("[Startup] Curse model warmed up successfully.")
    except Exception as e:
        print(f"[Startup] Curse model warmup failed: {e}")


@app.get("/health")
def health_check():
    """
    서버 헬스체크 엔드포인트
    """
    return {"status": "ok"}
