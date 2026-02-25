"""Shared pytest fixtures for sim-orchestrator tests."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


@pytest.fixture(autouse=True)
def mock_db_pool(monkeypatch):
    """Prevent asyncpg from trying to connect to a real database during tests."""
    fake_pool = AsyncMock()

    async def fake_create_pool(*args, **kwargs):
        return fake_pool

    monkeypatch.setattr("asyncpg.create_pool", fake_create_pool)
    return fake_pool


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """Prevent aioredis from trying to connect to a real Redis during tests."""
    fake_redis = AsyncMock()

    async def fake_from_url(*args, **kwargs):
        return fake_redis

    monkeypatch.setattr("redis.asyncio.from_url", fake_from_url)
    return fake_redis
