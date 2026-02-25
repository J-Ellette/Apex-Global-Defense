"""
agd_shared.errors — Canonical error response helpers for AGD Python services.

Provides consistent error shapes across all services so clients can rely on
a uniform error envelope regardless of which service they are calling.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Standard error response body."""

    code: str
    message: str
    detail: str | None = None


def error_response(
    status_code: int,
    code: str,
    message: str,
    detail: str | None = None,
) -> JSONResponse:
    """Return a JSONResponse with a canonical ErrorDetail body."""
    body = ErrorDetail(code=code, message=message, detail=detail)
    return JSONResponse(status_code=status_code, content=body.model_dump(exclude_none=True))


# ---------------------------------------------------------------------------
# Convenience factories for common error types
# ---------------------------------------------------------------------------


def not_found(resource: str, identifier: str | int | None = None) -> HTTPException:
    msg = f"{resource} not found"
    if identifier is not None:
        msg = f"{resource} '{identifier}' not found"
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)


def forbidden(reason: str = "Access denied") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=reason)


def bad_request(reason: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)


def internal_error(reason: str = "Internal server error") -> HTTPException:
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=reason)
