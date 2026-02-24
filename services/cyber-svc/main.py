from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import attacks, infrastructure, techniques

logger = logging.getLogger("cyber-svc")


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.db = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
    )
    logger.info("cyber-svc started")
    yield
    await application.state.db.close()
    logger.info("cyber-svc stopped")


app = FastAPI(
    title="AGD Cyber Operations Service",
    description="MITRE ATT&CK catalog, infrastructure graph, and cyber attack planning.",
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

app.include_router(techniques.router, prefix="/api/v1")
app.include_router(infrastructure.router, prefix="/api/v1")
app.include_router(attacks.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
