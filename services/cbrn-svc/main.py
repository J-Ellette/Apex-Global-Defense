from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import agents, releases

logger = logging.getLogger("cbrn-svc")


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.db = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
    )
    logger.info("cbrn-svc started")
    yield
    await application.state.db.close()
    logger.info("cbrn-svc stopped")


app = FastAPI(
    title="AGD CBRN Dispersion Service",
    description="CBRN agent catalog, release planning, and Gaussian plume dispersion modeling.",
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

app.include_router(agents.router, prefix="/api/v1")
app.include_router(releases.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
