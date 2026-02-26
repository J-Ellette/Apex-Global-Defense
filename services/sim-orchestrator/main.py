from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import asyncpg
import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import runs, scenarios

logger = logging.getLogger("sim-orchestrator")


# ---------------------------------------------------------------------------
# OpenTelemetry setup — call before app is constructed so middleware can see
# the configured TracerProvider.
# ---------------------------------------------------------------------------

def _configure_otel(app_name: str, otlp_endpoint: str) -> None:
    """Configure the global TracerProvider.

    Uses OTLP HTTP exporter when *otlp_endpoint* is set and the exporter
    package is installed, otherwise falls back to a no-op / console exporter
    suitable for dev.  The OTLP exporter package is optional because it
    carries a protobuf version constraint that may conflict with other
    services; see requirements.txt for details.
    """
    from opentelemetry import trace  # noqa: PLC0415
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource  # noqa: PLC0415
    from opentelemetry.sdk.trace import TracerProvider  # noqa: PLC0415
    from opentelemetry.sdk.trace.export import BatchSpanProcessor  # noqa: PLC0415

    resource = Resource(attributes={SERVICE_NAME: app_name})
    provider = TracerProvider(resource=resource)

    exporter = None
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  # noqa: PLC0415
            exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")
            logger.info("OpenTelemetry: OTLP HTTP exporter → %s", otlp_endpoint)
        except ImportError:
            logger.warning(
                "OTEL_EXPORTER_OTLP_ENDPOINT is set but opentelemetry-exporter-otlp-proto-http "
                "is not installed; falling back to console exporter."
            )

    if exporter is None:
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter  # noqa: PLC0415
        exporter = ConsoleSpanExporter()
        if not otlp_endpoint:
            logger.debug(
                "OpenTelemetry: console exporter active "
                "(set OTEL_EXPORTER_OTLP_ENDPOINT to ship traces to a collector)"
            )

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


_configure_otel(settings.otel_service_name, settings.otel_exporter_otlp_endpoint)


@asynccontextmanager
async def lifespan(application: FastAPI):
    # Connect to PostgreSQL
    application.state.db = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
    )
    # Connect to Redis
    application.state.redis = await aioredis.from_url(
        settings.redis_url, encoding="utf-8", decode_responses=True
    )
    logger.info("sim-orchestrator started")
    yield
    await application.state.db.close()
    await application.state.redis.close()
    logger.info("sim-orchestrator stopped")


app = FastAPI(
    title="AGD Simulation Orchestrator",
    description="Manages scenario lifecycle and dispatches simulation runs.",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# OpenTelemetry FastAPI instrumentation — must be called before middleware so
# that the OTel middleware wraps the outermost layer and captures all requests.
# ---------------------------------------------------------------------------
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # noqa: E402
FastAPIInstrumentor.instrument_app(app)

# ---------------------------------------------------------------------------
# Prometheus metrics — exposes /metrics for Prometheus scraping.
# ---------------------------------------------------------------------------
from prometheus_fastapi_instrumentator import Instrumentator  # noqa: E402
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scenarios.router, prefix="/api/v1")
app.include_router(runs.router, prefix="/api/v1")


@app.get("/health")
async def health():
    engine_mode = "grpc" if settings.use_grpc_sim_engine else "stub"
    return {
        "status": "ok",
        "engine_mode": engine_mode,
        "engine_addr": settings.sim_engine_grpc_addr if settings.use_grpc_sim_engine else None,
    }
