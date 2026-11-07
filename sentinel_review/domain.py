"""Strongly-typed, immutable domain models and validation rules for Cold-Chain Adjudication.

All records are validated fail-closed: missing, inverted, or non-finite measurements
immediately flag as UNKNOWN/INVALID and never default to compliant.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any
import hashlib
import json


def serialized(value: Any) -> str:
    """Deterministic JSON serialization with sorted keys and no non-finite floats."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def content_hash(value: Any) -> str:
    """Cryptographic SHA-256 fingerprint of any canonical serializable payload."""
    return hashlib.sha256(serialized(value).encode("utf-8")).hexdigest()


def utc(value: Any) -> datetime:
    """Parse timestamp into timezone-aware UTC datetime."""
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    else:
        raise ValueError("timestamp missing")
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def finite(value: Any) -> Decimal:
    """Parse numeric values into strict finite Decimals; booleans and missing values rejected."""
    if value is None or isinstance(value, bool):
        raise ValueError("numeric evidence missing")
    try:
        parsed = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("numeric evidence invalid") from exc
    if not parsed.is_finite():
        raise ValueError("numeric evidence nonfinite")
    return parsed


def normalized(value: Any) -> str:
    """Normalize strings for case-insensitive matching."""
    return " ".join(str(value or "").casefold().split())


def gtin(value: Any) -> str:
    """Normalize GTIN strings to 14-digit representation."""
    try:
        parsed = finite(value)
    except ValueError:
        return ""
    if parsed != parsed.to_integral_value() or parsed < 0:
        return ""
    digits = str(int(parsed))
    return digits.zfill(14) if len(digits) <= 14 else ""


class CaseStatus(str, Enum):
    BLOCKED = "BLOCKED"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    SIGNED = "SIGNED"


class MeasurementState(str, Enum):
    UNKNOWN = "UNKNOWN"
    SUMMARY_PRESENT_NOT_SERIES_VERIFIED = "SUMMARY_PRESENT_NOT_SERIES_VERIFIED"
    SERIES_VERIFIED = "SERIES_VERIFIED"


class ObligationState(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPLICABILITY_UNVERIFIED = "APPLICABILITY_UNVERIFIED"
    SUBMITTED = "SUBMITTED"


@dataclass(frozen=True)
class TenantScope:
    """Enforces tenant isolation invariants."""
    tenant: str

    def check(self, row: SourceRow) -> None:
        if not self.tenant or row.values.get("tenant_code") != self.tenant:
            raise PermissionError("event unavailable in tenant scope")


@dataclass(frozen=True)
class SourceRow:
    """Provenanced row originating from a specific sheet and row index."""
    sheet: str
    row: int
    values: dict[str, Any]

    def snapshot(self) -> dict[str, Any]:
        return {"sheet": self.sheet, "row": self.row, "values": dict(self.values)}


@dataclass(frozen=True)
class ExcursionEvent:
    """Validated excursion event data contract."""
    event_id: str
    tenant_code: str
    product_ref: str
    excursion_start_utc: datetime | None
    alert_ts_utc: datetime | None
    min_temp_c: Decimal | None
    max_temp_c: Decimal | None
    logger_fw: str
    regulator_reportable: str | None
    reg_window_hours: Decimal | None

    @classmethod
    def from_source_row(cls, row: SourceRow) -> ExcursionEvent:
        vals = row.values
        start = None
        alert = None
        try:
            start = utc(vals.get("excursion_start_utc"))
        except (ValueError, TypeError):
            pass
        try:
            alert = utc(vals.get("alert_ts_utc"))
        except (ValueError, TypeError):
            pass

        min_t = None
        max_t = None
        try:
            min_t = finite(vals.get("min_temp_c"))
        except ValueError:
            pass
        try:
            max_t = finite(vals.get("max_temp_c"))
        except ValueError:
            pass

        reg_win = None
        try:
            reg_win = finite(vals.get("reg_window_hours"))
        except ValueError:
            pass

        return cls(
            event_id=str(vals.get("event_id", "")),
            tenant_code=str(vals.get("tenant_code", "")),
            product_ref=str(vals.get("product_ref_as_received", "")),
            excursion_start_utc=start,
            alert_ts_utc=alert,
            min_temp_c=min_t,
            max_temp_c=max_t,
            logger_fw=str(vals.get("logger_fw", "")),
            regulator_reportable=vals.get("regulator_reportable"),
            reg_window_hours=reg_win,
        )


@dataclass(frozen=True)
class ResolutionTask:
    """A role-assigned action required to clear an unverified hold or ambiguity."""
    id: str
    reason: str
    role: str
    evidence_requested: str
    completion_criterion: str
    sources: list[dict[str, Any]]
    status: str = "OPEN"
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "reason": self.reason,
            "role": self.role,
            "evidence_requested": self.evidence_requested,
            "completion_criterion": self.completion_criterion,
            "sources": self.sources,
            "status": self.status,
            "detail": self.detail,
        }
