"""SQLite adapter: transactional evidence bundles plus separately admitted obligations."""
import json
import sqlite3
from datetime import timedelta
from .domain import SourceRow, TenantScope, content_hash, finite, serialized, utc


class SQLiteRepository:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS bundles(tenant TEXT NOT NULL, id TEXT NOT NULL,
          payload TEXT NOT NULL, PRIMARY KEY(tenant,id));
        CREATE TABLE IF NOT EXISTS obligations(tenant TEXT NOT NULL,event_id TEXT NOT NULL,
          reportability TEXT NOT NULL,due_utc TEXT,state TEXT NOT NULL,basis TEXT NOT NULL,
          PRIMARY KEY(tenant,event_id));
        """)
        self.db.commit()

    def register_obligation(self, event: SourceRow, tenant: str) -> None:
        TenantScope(tenant).check(event)
        raw = event.values.get("regulator_reportable")
        reportability = {"Y": "IMPORTED_REPORTABLE", "N": "IMPORTED_NOT_REPORTABLE"}.get(raw, "UNKNOWN")
        due = None
        if raw == "Y":
            try:
                hours = finite(event.values.get("reg_window_hours"))
                if hours <= 0:
                    raise ValueError("nonpositive window")
                due = (utc(event.values["alert_ts_utc"]) + timedelta(seconds=float(hours * 3600))).isoformat()
            except (ValueError, TypeError, KeyError, OverflowError):
                due = None
        state = "PENDING_REVIEW" if raw == "Y" and due else "APPLICABILITY_UNVERIFIED"
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO obligations VALUES(?,?,?,?,?,?)", (
                tenant, event.values["event_id"], reportability, due, state,
                "Historical reportability/window imported; NOT legal or calendar qualification"))

    def obligations(self, tenant):
        cols = ("event_id", "reportability", "due_utc", "state", "basis")
        return [dict(zip(cols, r)) for r in self.db.execute(
            "SELECT event_id,reportability,due_utc,state,basis FROM obligations "
            "WHERE tenant=? ORDER BY due_utc,event_id",
            (tenant,))]

    def save(self, tenant, payload):
        if payload["result"]["tenant"] != tenant or payload["captured"]["event"]["values"].get("tenant_code") != tenant:
            raise PermissionError("bundle tenant mismatch")
        key = content_hash(payload)
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO bundles VALUES(?,?,?)", (tenant, key, serialized(payload)))
        return key

    def read(self, tenant, key):
        row = self.db.execute("SELECT payload FROM bundles WHERE tenant=? AND id=?", (tenant, key)).fetchone()
        if row is None:
            raise LookupError("bundle unavailable to tenant")
        payload = json.loads(row[0])
        if content_hash(payload) != key:
            raise ValueError("bundle integrity failure")
        return payload

    def close(self):
        self.db.close()
