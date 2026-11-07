"""Mock WORM archive for local testing and CI without cloud storage.

Uses in-memory dict. For production, swap in S3 Object Lock or Azure Immutable Blob.
"""
from __future__ import annotations
import hashlib
import json
from typing import Any


class MockWormArchive:
    """In-memory WORM archive for testing. Write-once semantics enforced."""

    def __init__(self, retention_years: int = 7):
        self.store: dict[str, dict[str, Any]] = {}
        self.retention_years = retention_years

    def write(self, tenant: str, key: str, payload: dict[str, Any]) -> str:
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        full_key = f"{tenant}:{key}:{digest[:16]}"
        if full_key in self.store:
            raise FileExistsError(f"archive entry already exists: {full_key}")
        self.store[full_key] = payload
        return full_key

    def read(self, tenant: str, key: str) -> dict[str, Any] | None:
        for k, v in self.store.items():
            if k.startswith(f"{tenant}:{key}:"):
                return v
        return None

    def verify_retention(self, tenant: str, key: str, now: float) -> bool:
        payload = self.read(tenant, key)
        if payload is None:
            return False
        created = payload.get("created_at", 0)
        return (now - created) < (self.retention_years * 365 * 24 * 3600)
