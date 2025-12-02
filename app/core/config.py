# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List

from pathlib import Path


class Settings(BaseSettings):
    # --- 앱 기본 ---
    APP_NAME: str = Field(default="gangku-ai-server")
    ENV: str = Field(default="local")
    DEBUG: bool = Field(default=True)
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8000)

    # --- 외부 연동 (필요 시) ---
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str | None = None

    # --- 로컬 욕설 모델 ---
    CURSE_MODEL_ID: str = Field(default="2tle/korean-curse-detection")

    # --- 블랙리스트 파일 경로(선택) ---
    BLACKLIST_PATH: str | None = Field(default=None)

    # --- XLMR HTTP API ---
    XLMR_BASE_URL: str | None = None
    XLMR_PATH: str = Field(default="/xlmr-large-toxicity-classifier")
    XLMR_API_KEY: str | None = None
    # 타임아웃/재시도/서킷브레이커 쿨다운(운영 정책)
    XLMR_TIMEOUT: float | None = None
    XLMR_RETRIES: int | None = None
    XLMR_CB_COOLDOWN_SEC: int | None = None

    # --- CORS/로깅 ---
    CORS_ORIGINS: List[str] = Field(default_factory=list)
    LOG_LEVEL: str = Field(default="INFO")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # .env에서 소문자/대문자 모두 허용
        extra="ignore",
    )

    # --- RECOMMANDATIONS ----
    RECOMMANDS_LIMIT: int | None = None
    RECOMMENDER_N_CLUSTERS: int | None = None
    RECOMMENDER_SVD_DIM: int | None = None

    # 아티팩트 dir
    CLUSTER_ARTIFACT_DIR: Path = Path("app/cluster/artifacts/user_clustering")
    POPULARITY_ARTIFACT_DIR: Path = Path("app/cluster/artifacts/popularity")


settings = Settings()
