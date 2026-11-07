"""Pure domain helpers: deterministic hashing, parsing and tenant scope. No I/O."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
import hashlib
import json


def serialized(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def content_hash(value: Any) -> str:
    return hashlib.sha256(serialized(value).encode()).hexdigest()


def utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    else:
        raise ValueError("timestamp missing")
    # Only fields labelled UTC in the source are passed here.
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def finite(value: Any) -> Decimal:
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
    return " ".join(str(value or "").casefold().split())


def gtin(value: Any) -> str:
    """Normalize spreadsheet GTIN forms for lookup only; no check-digit authority."""
    try:
        parsed = finite(value)
    except ValueError:
        return ""
    if parsed != parsed.to_integral_value() or parsed < 0:
        return ""
    digits = str(int(parsed))
    return digits.zfill(14) if len(digits) <= 14 else ""


@dataclass(frozen=True)
class SourceRow:
    sheet: str
    row: int
    values: dict[str, Any]

    def snapshot(self) -> dict[str, Any]:
        return {"sheet": self.sheet, "row": self.row, "values": dict(self.values)}


@dataclass(frozen=True)
class TenantScope:
    tenant: str

    def check(self, row: SourceRow) -> None:
        if not self.tenant or row.values.get("tenant_code") != self.tenant:
            raise PermissionError("event unavailable in tenant scope")
