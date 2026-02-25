from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

bearer_scheme = HTTPBearer(auto_error=False)

# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

# Ordered classification levels (lower index = less sensitive)
_CLASSIFICATION_ORDER: dict[str, int] = {
    "UNCLASS": 0,
    "FOUO": 1,
    "SECRET": 2,
    "TOP_SECRET": 3,
    "TS_SCI": 4,
}

# All levels that are at-or-below a given clearance ceiling
_ALLOWED_LEVELS: dict[str, list[str]] = {
    "UNCLASS":    ["UNCLASS"],
    "FOUO":       ["UNCLASS", "FOUO"],
    "SECRET":     ["UNCLASS", "FOUO", "SECRET"],
    "TOP_SECRET": ["UNCLASS", "FOUO", "SECRET", "TOP_SECRET"],
    "TS_SCI":     ["UNCLASS", "FOUO", "SECRET", "TOP_SECRET", "TS_SCI"],
}


def get_user_classification(user: dict) -> str:
    """Return the classification ceiling string from the JWT claims (default UNCLASS)."""
    raw = user.get("cls", 0)
    # cls is stored as an integer in the JWT (0-4)
    by_int = {v: k for k, v in _CLASSIFICATION_ORDER.items()}
    if isinstance(raw, int):
        return by_int.get(raw, "UNCLASS")
    if isinstance(raw, str) and raw in _CLASSIFICATION_ORDER:
        return raw
    return "UNCLASS"


def classification_allowed_levels(user_cls: str) -> list[str]:
    """Return all classification levels visible to a user with the given ceiling."""
    return _ALLOWED_LEVELS.get(user_cls, ["UNCLASS"])


def enforce_classification_ceiling(user: dict, record_cls: str) -> None:
    """
    Raise HTTP 403 if the record's classification exceeds the user's clearance.
    Call this before returning or writing a record.
    """
    user_cls = get_user_classification(user)
    user_rank = _CLASSIFICATION_ORDER.get(user_cls, 0)
    record_rank = _CLASSIFICATION_ORDER.get(record_cls, 0)
    if record_rank > user_rank:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient clearance: record is {record_cls}, user ceiling is {user_cls}",
        )


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return payload


def require_permission(user: dict, permission: str) -> None:
    perms: list[str] = user.get("perms", [])
    if permission not in perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing permission: {permission}",
        )
