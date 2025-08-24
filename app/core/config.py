from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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
    GOOGLE_CLIENT_SECRET: str | None = None # 웹 클라에만 필요
    GOOGLE_REDIRECT_URI: str | None = None # 웹 클라에만 필요
    GOOGLE_CLIENT_ID_WEB: str | None = None # 웹 클라에만 필요

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
