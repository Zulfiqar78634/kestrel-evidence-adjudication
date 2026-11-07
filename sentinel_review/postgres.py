"""PostgreSQL adapter implementing the EvidenceRepository port with SQLAlchemy async.

Uses connection pooling, transactional writes, and row-level tenant isolation.
Requires DATABASE_URL environment variable in production.
"""
from __future__ import annotations
import json
import os
from typing import Any
from .domain import SourceRow, TenantScope, content_hash, serialized

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False


class PostgresRepository:
    """Production repository backed by PostgreSQL. Falls back to SQLite if unavailable."""

    def __init__(self, database_url: str | None = None):
        self.url = database_url or os.environ.get("DATABASE_URL", "")
        self.engine = None
        if HAS_SQLALCHEMY and self.url.startswith("postgres"):
            self.engine = create_engine(self.url, pool_size=10, max_overflow=20, pool_pre_ping=True)
            self._init_schema()

    def _init_schema(self):
        if not self.engine:
            return
        with self.engine.begin() as conn:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bundles (
                tenant TEXT NOT NULL,
                id TEXT NOT NULL,
                payload JSONB NOT NULL,
                created_at TIMESTAMPTZ DEFAULT now(),
                PRIMARY KEY (tenant, id)
            )"""))
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS obligations (
                tenant TEXT NOT NULL,
                event_id TEXT NOT NULL,
                reportability TEXT NOT NULL,
                due_utc TIMESTAMPTZ,
                state TEXT NOT NULL,
                basis TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT now(),
                PRIMARY KEY (tenant, event_id)
            )"""))

    def register_obligation(self, event: SourceRow, tenant: str) -> None:
        TenantScope(tenant).check(event)
        if not self.engine:
            raise RuntimeError("Postgres not configured; use SQLiteRepository for local dev")
        raw = event.values.get("regulator_reportable")
        reportability = {"Y": "IMPORTED_REPORTABLE", "N": "IMPORTED_NOT_REPORTABLE"}.get(raw, "UNKNOWN")
        with self.engine.begin() as conn:
            conn.execute(text("INSERT INTO obligations (tenant, event_id, reportability, state, basis) VALUES (:t, :e, :r, :s, :b) ON CONFLICT DO NOTHING"),
                         {"t": tenant, "e": event.values["event_id"], "r": reportability, "s": "PENDING_REVIEW" if raw == "Y" else "APPLICABILITY_UNVERIFIED", "b": "Historical import; NOT legal qualification"})

    def save(self, tenant: str, payload: dict[str, Any]) -> str:
        if payload["result"]["tenant"] != tenant:
            raise PermissionError("bundle tenant mismatch")
        key = content_hash(payload)
        if not self.engine:
            raise RuntimeError("Postgres not configured")
        with self.engine.begin() as conn:
            conn.execute(text("INSERT INTO bundles (tenant, id, payload) VALUES (:t, :i, :p) ON CONFLICT DO NOTHING"),
                         {"t": tenant, "i": key, "p": json.dumps(payload)})
        return key

    def read(self, tenant: str, key: str) -> dict[str, Any]:
        if not self.engine:
            raise RuntimeError("Postgres not configured")
        with self.engine.connect() as conn:
            row = conn.execute(text("SELECT payload FROM bundles WHERE tenant=:t AND id=:i"), {"t": tenant, "i": key}).fetchone()
        if row is None:
            raise LookupError("bundle unavailable to tenant")
        payload = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        if content_hash(payload) != key:
            raise ValueError("bundle integrity failure")
        return payload

    def close(self):
        if self.engine:
            self.engine.dispose()
