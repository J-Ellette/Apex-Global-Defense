"""Shared pytest fixtures for cyber-svc tests."""

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
