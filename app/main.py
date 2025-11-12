"""FastAPI 메인 엔트리포인트 (AI 서버)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import autowrite

# --------------------------------------------------
# ✅ FastAPI 앱 생성
# --------------------------------------------------
app = FastAPI(
    title="GangKU AI Server",
    description="건국대학교 강쿠 AI 마이크로서비스 (모임 자동 소개문 등)",
    version="1.0.0",
)

# --------------------------------------------------
# ✅ CORS 설정
# (로컬 프론트엔드, 외부 도메인 접근 허용)
# --------------------------------------------------
origins = [
    "http://localhost",
    "http://localhost:3000",  # Next.js / React 로컬 개발용
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# ✅ API 라우터 등록
# --------------------------------------------------
app.include_router(autowrite.router)


# --------------------------------------------------
# ✅ 루트 헬스체크
# --------------------------------------------------
@app.get("/", tags=["Health"])
async def root() -> dict:
    """서버 상태 확인용 엔드포인트"""
    return {"message": "GangKU AI Server is running 🚀"}


# --------------------------------------------------
# ✅ 로컬 실행 가이드
# --------------------------------------------------
# python -m uvicorn app.main:app --reload
