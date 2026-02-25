# agd-shared

Shared internal Python library for all AGD Python microservices.

## Modules

| Module | Description |
|--------|-------------|
| `agd_shared.auth` | JWT validation, classification helpers (`get_user_classification`, `classification_allowed_levels`, `enforce_classification_ceiling`, `get_current_user`, `require_permission`) |
| `agd_shared.errors` | Canonical error response factories (`not_found`, `forbidden`, `bad_request`, `internal_error`) |

## Installing in a service

Add to the service's `requirements.txt` (local editable install, works in Docker):

```
-e ../../agd-shared
```

Or for a containerised build, copy the package directory and install it:

```dockerfile
COPY ../agd-shared /agd-shared
RUN pip install /agd-shared
```

## Usage

```python
from agd_shared.auth import get_current_user, enforce_classification_ceiling
from agd_shared.errors import not_found

@router.get("/items/{item_id}")
async def get_item(item_id: str, user: dict = Depends(get_current_user)):
    item = await db.fetch_item(item_id)
    if item is None:
        raise not_found("Item", item_id)
    enforce_classification_ceiling(user, item["classification"])
    return item
```

## Migration from per-service auth.py

Each Python service currently contains an identical copy of `app/auth.py`.
To migrate a service:

1. Add `agd-shared` to its `requirements.txt`.
2. Replace `from app.auth import ...` with `from agd_shared.auth import ...`.
3. Delete the now-redundant `app/auth.py`.
4. The service's `app/config.settings.jwt_secret` is no longer read by the shared
   auth module — it reads `JWT_SECRET` directly from the environment, which is
   already the source of truth for all services.
