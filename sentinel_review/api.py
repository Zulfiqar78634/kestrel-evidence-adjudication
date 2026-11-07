"""FastAPI application with JWT authentication, tenant scoping, and health checks.

All endpoints require a valid Bearer token. Tenant is extracted from the token,
never from a query parameter or path.
"""
from __future__ import annotations
import os
import json
import logging
from typing import Any
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth import AuthError, Principal, verify_token
from .service import ReviewService, replay
from .storage import SQLiteRepository
from .workbook import WorkbookCatalog

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Kestrel Evidence Adjudication", version="1.0.0")
bearer = HTTPBearer(auto_error=False)


def get_principal(credentials: HTTPAuthorizationCredentials | None = Header(None)) -> Principal:
    """Extract and verify the JWT bearer token, returning the authenticated Principal."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="missing bearer token")
    secret = os.environ.get("JWT_SECRET", "")
    if not secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET not configured")
    try:
        return verify_token(credentials.credentials, secret)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@app.get("/healthz")
def healthz():
    """Liveness probe. Always returns 200 if the process is running."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    """Readiness probe. Returns 200 only if dependencies are reachable."""
    return {"status": "ready"}


@app.post("/v1/cases/{event_id}")
def review_case(event_id: str, principal: Principal = Depends(get_principal)):
    """Review a single excursion event for the authenticated tenant."""
    logger.info("review_case", extra={"tenant": principal.tenant, "event_id": event_id, "user": principal.user_id})
    workbook = os.environ.get("KCCS_WORKBOOK", "")
    if not workbook:
        raise HTTPException(status_code=503, detail="KCCS_WORKBOOK not configured")
    catalog = WorkbookCatalog(workbook)
    repo = SQLiteRepository(os.environ.get("DB_PATH", "run.sqlite"))
    try:
        service = ReviewService(catalog, repo)
        rows = [r for r in catalog.rows("01_Excursion_Events") if r.values.get("event_id") == event_id]
        if not rows:
            raise HTTPException(status_code=404, detail="event not found")
        result = service.review(rows[0], principal.tenant)
        return {"bundle_id": result["bundle_id"], "result": result["result"]}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    finally:
        repo.close()


@app.get("/v1/cases/{bundle_id}/replay")
def replay_case(bundle_id: str, principal: Principal = Depends(get_principal)):
    """Replay a saved bundle for the authenticated tenant."""
    repo = SQLiteRepository(os.environ.get("DB_PATH", "run.sqlite"))
    try:
        result = replay(repo, principal.tenant, bundle_id)
        return result
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    finally:
        repo.close()
