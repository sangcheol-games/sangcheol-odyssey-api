import os
from pathlib import Path
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

# 프로젝트 루트 디렉토리 설정 (app/core/config.py 기준 세 단계 위)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    # env_file을 절대 경로로 지정하여 실행 위치와 상관없이 .env를 로드하도록 함
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, 
        extra="ignore",
        env_file_encoding='utf-8'
    )

    APP_ENV: str = "dev"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    API_V1_STR: str = "/v1"

    DB_HOST: str = "localhost"
    DB_PORT: int = 55432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "sangcheol"

    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str = ""
    JWT_EXPIRES_SEC: int = 3600
    REFRESH_EXPIRES_SEC: int = 30 * 24 * 3600
    REFRESH_REDIS_PREFIX: str = "rtk:"
    REFRESH_USER_SET_PREFIX: str = "rtu:"
    REFRESH_HASH_PEPPER: str | None = None

    GOOGLE_CLIENT_IDS: str = ""
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None
    GOOGLE_CLIENT_ID_WEB: str | None = None

    STEAM_WEB_API_KEY: str = ""
    STEAM_APP_ID: str = "4566350"

    @property
    def db_url_async(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def db_url_sync(self) -> str:
        return (
            f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def google_client_id_list(self) -> list[str]:
        return [s.strip() for s in self.GOOGLE_CLIENT_IDS.split(",") if s.strip()]


settings = Settings()

logger = logging.getLogger(__name__)

logger.info(f"Looking for .env at: {ENV_FILE}")
if ENV_FILE.exists():
    logger.info(".env file found.")
else:
    logger.warning(f".env file NOT found at {ENV_FILE}")

if settings.STEAM_WEB_API_KEY:
    logger.info("Steam Web API Key is configured.")
else:
    logger.error("STEAM_WEB_API_KEY is EMPTY in Settings!")
