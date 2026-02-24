from __future__ import annotations

from fastapi import HTTPException, Request
from jose import JWTError, jwt

from app.config import settings


def get_current_user(request: Request) -> dict:
    """Extract and validate JWT from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc
    return payload


def require_permission(payload: dict, permission: str) -> None:
    """Raise 403 if the JWT payload lacks the required permission."""
    perms: list[str] = payload.get("perms", [])
    if permission not in perms:
        raise HTTPException(
            status_code=403,
            detail=f"Permission required: {permission}",
        )
