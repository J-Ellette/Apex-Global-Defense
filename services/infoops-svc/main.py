from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import narratives, campaigns, indicators, attribution

logger = logging.getLogger("infoops-svc")


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.db = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
    )
    logger.info("infoops-svc started")
    yield
    await application.state.db.close()
    logger.info("infoops-svc stopped")


app = FastAPI(
    title="AGD Information Operations Service",
    description=(
        "Information operations tracking, disinformation analysis, influence campaign monitoring, "
        "and narrative threat assessment for strategic information warfare operations."
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

app.include_router(narratives.router, prefix="/api/v1")
app.include_router(campaigns.router, prefix="/api/v1")
app.include_router(indicators.router, prefix="/api/v1")
app.include_router(attribution.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
