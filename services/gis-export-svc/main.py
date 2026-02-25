from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import export, integrations

logger = logging.getLogger("gis-export-svc")


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.db = await asyncpg.create_pool(
        settings.database_url,
        min_size=2,
        max_size=10,
    )
    logger.info("gis-export-svc started")
    yield
    await application.state.db.close()
    logger.info("gis-export-svc stopped")


app = FastAPI(
    title="AGD GIS Export Service",
    description=(
        "GIS format export and external system integration for ArcGIS, Google Earth, "
        "WMS/WFS, and other geospatial platforms."
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

app.include_router(export.router, prefix="/api/v1")
app.include_router(integrations.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
