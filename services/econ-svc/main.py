from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import sanctions, trade, impact

logger = logging.getLogger("econ-svc")


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.db = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
    )
    logger.info("econ-svc started")
    yield
    await application.state.db.close()
    logger.info("econ-svc stopped")


app = FastAPI(
    title="AGD Economic Warfare Service",
    description=(
        "Economic pressure modeling, sanctions tracking, trade disruption analysis, "
        "and GDP impact assessment for strategic economic warfare operations."
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

app.include_router(sanctions.router, prefix="/api/v1")
app.include_router(trade.router, prefix="/api/v1")
app.include_router(impact.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
