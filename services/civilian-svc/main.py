from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import corridors, flows, impact, population

logger = logging.getLogger("civilian-svc")


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.db = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
    )
    logger.info("civilian-svc started")
    yield
    await application.state.db.close()
    logger.info("civilian-svc stopped")


app = FastAPI(
    title="AGD Civilian Impact Service",
    description=(
        "Population zone management, conflict civilian impact assessment, "
        "refugee flow modeling, and humanitarian corridor tracking."
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

app.include_router(population.router, prefix="/api/v1")
app.include_router(impact.router, prefix="/api/v1")
app.include_router(flows.router, prefix="/api/v1")
app.include_router(corridors.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
