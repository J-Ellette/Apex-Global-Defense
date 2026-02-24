from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analysis, plans, scenarios, sites

logger = logging.getLogger("terror-svc")


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.db = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
    )
    logger.info("terror-svc started")
    yield
    await application.state.db.close()
    logger.info("terror-svc stopped")


app = FastAPI(
    title="AGD Terror Response Planning Service",
    description="Target site vulnerability assessment, threat scenario planning, and multi-agency response coordination.",
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

app.include_router(sites.router, prefix="/api/v1")
app.include_router(scenarios.router, prefix="/api/v1")
app.include_router(plans.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
