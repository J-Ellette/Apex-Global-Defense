from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import exercises, injects, objectives

logger = logging.getLogger("training-svc")


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.db = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
    )
    logger.info("training-svc started")
    yield
    await application.state.db.close()
    logger.info("training-svc stopped")


app = FastAPI(
    title="AGD Training Service",
    description=(
        "Exercise management, scripted inject system, and trainee performance scoring "
        "for AGD training mode operations."
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

app.include_router(exercises.router, prefix="/api/v1")
app.include_router(injects.router, prefix="/api/v1")
app.include_router(objectives.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
