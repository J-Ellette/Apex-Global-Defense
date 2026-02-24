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
    return {"status": "ok"}
