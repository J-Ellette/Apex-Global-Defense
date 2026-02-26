from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql://agd:devpass@localhost:5432/agd_dev"
    redis_url: str = "redis://localhost:6379"
    jwt_secret: str = "dev-secret-change-in-prod"
    jwt_algorithm: str = "HS256"
    sim_engine_grpc_addr: str = "sim-engine:50051"
    use_grpc_sim_engine: bool = False
    port: int = 8000
    env: str = "development"
    cors_origins: list[str] = ["*"]

    # OpenTelemetry — set OTEL_EXPORTER_OTLP_ENDPOINT to enable OTLP export.
    # Leave empty to use the console (stdout) exporter in dev.
    otel_service_name: str = "sim-orchestrator"
    otel_exporter_otlp_endpoint: str = ""


settings = Settings()
