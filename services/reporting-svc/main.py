from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import reports

logger = logging.getLogger("reporting-svc")


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.db = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
    )
    logger.info("reporting-svc started")
    yield
    await application.state.db.close()
    logger.info("reporting-svc stopped")


app = FastAPI(
    title="AGD Reporting Service",
    description=(
        "Auto-report generation for SITREP, INTSUM, and CONOPS briefs. "
        "Aggregates simulation and intelligence data into structured NATO-format reports."
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

app.include_router(reports.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
