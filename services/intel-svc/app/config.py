from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql://agd:devpass@localhost:5432/agd_dev"
    jwt_secret: str = "dev-secret-change-in-prod"
    jwt_algorithm: str = "HS256"
    port: int = 8000
    env: str = "development"
    cors_origins: list[str] = ["*"]

    # OSINT adapter config (optional; adapters run in stub mode if not set)
    acled_api_key: str = ""
    acled_email: str = ""
    ucdp_api_key: str = ""


settings = Settings()
