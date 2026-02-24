from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analysis, cells, incidents

logger = logging.getLogger("asym-svc")


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.db = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
    )
    logger.info("asym-svc started")
    yield
    await application.state.db.close()
    logger.info("asym-svc stopped")


app = FastAPI(
    title="AGD Asymmetric / Insurgency Service",
    description="Insurgent cell network modeling, IED threat tracking, and COIN planning.",
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

app.include_router(cells.router, prefix="/api/v1")
app.include_router(incidents.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
