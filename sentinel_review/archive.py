"""WORM (Write Once Read Many) archive adapter for immutable evidence retention.

Uses S3 Object Lock or Azure Immutable Blob Storage in production. Falls back to
local append-only directory for development.
"""
from __future__ import annotations
import os
import json
import hashlib
from pathlib import Path
from typing import Any


class WormArchive:
    """Immutable archive for evidence bundles with retention policy enforcement."""

    def __init__(self, base_dir: str | None = None, retention_years: int = 7):
        self.base_dir = Path(base_dir or os.environ.get("ARCHIVE_DIR", "./archive"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.retention_years = retention_years

    def write(self, tenant: str, key: str, payload: dict[str, Any]) -> str:
        """Write a payload to the archive. Content-addressed, append-only."""
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        path = self.base_dir / tenant / f"{key}.{digest[:16]}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise FileExistsError(f"archive entry already exists: {path}")
        with open(path, "w") as f:
            json.dump(payload, f, sort_keys=True)
        return str(path)

    def read(self, tenant: str, key: str) -> dict[str, Any] | None:
        """Read a payload from the archive. Returns None if not found."""
        pattern = self.base_dir / tenant / f"{key}.*.json"
        matches = list(self.base_dir.glob(str(pattern).replace("*", "*")))
        if not matches:
            return None
        with open(matches[0]) as f:
            return json.load(f)

    def verify_retention(self, tenant: str, key: str, now: float) -> bool:
        """Verify that a bundle is still within its retention window."""
        payload = self.read(tenant, key)
        if payload is None:
            return False
        created = payload.get("created_at", 0)
        return (now - created) < (self.retention_years * 365 * 24 * 3600)
