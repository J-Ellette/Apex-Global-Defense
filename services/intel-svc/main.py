from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.engine.osint_adapters import _init_registry
from app.routers import analysis, intel, osint

logger = logging.getLogger("intel-svc")


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.db = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
    )
    # Initialize OSINT adapter registry with configured credentials
    _init_registry(
        acled_key=settings.acled_api_key,
        acled_email=settings.acled_email,
        ucdp_key=settings.ucdp_api_key,
        recorded_future_key=settings.recorded_future_api_key,
        maxar_key=settings.maxar_api_key,
        janes_key=settings.janes_api_key,
    )
    logger.info("intel-svc started")
    yield
    await application.state.db.close()
    logger.info("intel-svc stopped")


app = FastAPI(
    title="AGD Intelligence Service",
    description=(
        "Intelligence item ingestion, AI-assisted entity extraction, "
        "threat assessment, OSINT pipeline (ACLED/UCDP/RSS), "
        "and pgvector semantic search."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intel.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(osint.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
