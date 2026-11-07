"""Narrow replaceable contracts; application code depends on these, not on adapters."""
from typing import Protocol
from .domain import SourceRow


class SourceCatalog(Protocol):
    """Read-only source rows. rows() must raise ValueError for a sheet it does not have."""

    def rows(self, sheet: str) -> tuple[SourceRow, ...]: ...


class EvidenceRepository(Protocol):
    def register_obligation(self, event: SourceRow, tenant: str) -> None: ...
    def save(self, tenant: str, payload: dict) -> str: ...
    def read(self, tenant: str, key: str) -> dict: ...
