"""Offline evidence-readiness kernel. No clinical disposition authority."""
import argparse
import hashlib
import json
import re
import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation

VERSION = "0.1.0"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def number(value):
    if value is None or isinstance(value, bool):
        raise ValueError("Finite number required")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Finite number required") from exc
    if not result.is_finite():
        raise ValueError("Finite number required")
    return result


def instant(value):
    if not isinstance(value, str):
        raise ValueError("Timezone-aware ISO timestamp required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() is None:
        raise ValueError("Timezone required")
    return result


def parse_limits(text):
    if not isinstance(text, str):
        raise ValueError("Storage instruction required")
    text = text.strip().lower().replace("−", "-").replace("–", "-")
    n = r"(-?\d+(?:\.\d+)?)"
    match = re.fullmatch(n + r"\s*(?:to|-)\s*" + n + r"\s*°?\s*c", text)
    if match:
        low, high = map(number, match.groups())
        if low > high:
            raise ValueError("Reversed bounds")
        return low, high, True, True
    match = re.fullmatch(r"(below|above|<=|>=|≤|≥)\s*" + n + r"\s*°?\s*c", text)
    if not match:
        raise ValueError("Unrecognized instruction; reviewed interpretation required")
    op, value = match.groups()
    value = number(value)
    return (None, value, True, op != "below") if op in ("below", "<=", "≤") else (value, None, op != "above", True)


def temperature_state(readings, limits, error_bound=0):
    low, high, low_inc, high_inc = limits
    error = number(error_bound)
    if error < 0:
        raise ValueError("Negative uncertainty")
    minimum = number(readings["min_c"]) if readings.get("min_c") is not None else None
    maximum = number(readings["max_c"]) if readings.get("max_c") is not None else None
    if (low is not None and minimum is None) or (high is not None and maximum is None):
        raise ValueError("Required extrema missing; mean is not a substitute")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("Reversed extrema")
    def below(v):
        return v < low or (v == low and not low_inc)
    def above(v):
        return v > high or (v == high and not high_inc)
    definite = (low is not None and below(minimum + error)) or (high is not None and above(maximum))
    possible = (low is not None and below(minimum)) or (high is not None and above(maximum + error))
    return "OUTSIDE" if definite else "UNCERTAIN" if possible else "WITHIN"


def evaluate(case, tenant):
    if not tenant or case.get("tenant_id") != tenant:
        raise PermissionError("Tenant mismatch")
    if not isinstance(case.get("event_id"), str) or not case["event_id"].strip():
        raise ValueError("event_id required")
    issues = []
    when = None
    try:
        when = instant(case.get("excursion_start"))
        if instant(case.get("alert_received")) < when:
            issues.append("INVALID_EVENT_ORDER")
    except (ValueError, TypeError):
        issues.append("INVALID_EVENT_TIME")
    try:
        state = temperature_state(case.get("measurements", {}), parse_limits(case.get("storage_instruction")), case.get("under_reading_bound_c", 0))
    except (ValueError, TypeError, AttributeError, KeyError):
        state = "UNKNOWN"
        issues.append("TEMPERATURE_UNRESOLVED")
    evidence = case.get("evidence", [])
    if not isinstance(evidence, list) or any(not isinstance(r, dict) for r in evidence):
        raise ValueError("evidence must be a list of objects")
    for kind in ("identity", "storage_spec", "telemetry", "sop", "stability"):
        records = [r for r in evidence if r.get("kind") == kind]
        if len(records) != 1:
            issues.append(kind.upper() + "_MISSING_OR_AMBIGUOUS")
            continue
        r = records[0]
        valid = (r.get("tenant_id") == tenant and r.get("approved") is True
                 and bool(case.get("product_id")) and r.get("product_id") == case["product_id"]
                 and bool(r.get("id")) and bool(r.get("approved_by"))
                 and isinstance(r.get("sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", r["sha256"]))
        if kind in ("sop", "storage_spec"):
            valid = valid and bool(case.get("site_id")) and r.get("site_id") == case["site_id"]
        if kind == "stability":
            valid = valid and bool(case.get("presentation")) and r.get("presentation") == case["presentation"]
        try:
            start = instant(r.get("valid_from"))
            end = instant(r["valid_to"]) if r.get("valid_to") else None
            valid = valid and when is not None and start <= when and (end is None or when < end)
        except (ValueError, TypeError):
            valid = False
        if not valid:
            issues.append(kind.upper() + "_AUTHORITY_UNRESOLVED")
    if state == "UNCERTAIN":
        issues.append("CALIBRATION_SENSITIVITY")
    if case.get("additional_constraints"):
        issues.append("ADDITIONAL_CONSTRAINTS_REQUIRE_REVIEW")
    if case.get("requires_batch_history") or case.get("once_only"):
        issues.append("EXPOSURE_HISTORY_AND_POLICY_REQUIRE_QA")
    status = "EVIDENCE_INCOMPLETE" if issues else "CLOSURE_CANDIDATE" if state == "WITHIN" else "READY_FOR_QA"
    return {"event_id": case["event_id"], "tenant_id": tenant, "version": VERSION,
            "input_sha256": digest(case), "status": status, "temperature_state": state,
            "issues": sorted(set(issues)), "human_disposition_required": True}


class Archive:
    """Atomic local snapshots; not WORM, authentication, or a seven-year archive."""
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS snapshots (tenant TEXT, id TEXT, payload TEXT NOT NULL, PRIMARY KEY(tenant,id))")
        self.db.commit()

    def save(self, case, tenant):
        result = evaluate(case, tenant)
        payload = {"case": case, "result": result, "version": VERSION}
        key = digest(payload)
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO snapshots VALUES (?,?,?)", (tenant, key, canonical(payload)))
        return key, result

    def replay(self, key, tenant):
        row = self.db.execute("SELECT payload FROM snapshots WHERE tenant=? AND id=?", (tenant, key)).fetchone()
        if row is None:
            raise LookupError("Snapshot unavailable to tenant")
        payload = json.loads(row[0])
        if digest(payload) != key:
            raise ValueError("Snapshot integrity failure")
        if payload["version"] != VERSION:
            raise ValueError("Archived evaluator unavailable")
        if evaluate(payload["case"], tenant) != payload["result"]:
            raise ValueError("Replay divergence")
        return {"identical": True, "snapshot_id": key, "result": payload["result"]}

    def close(self):
        self.db.close()


def demo():
    """Synthetic assertions, not verified source documents or real clinical facts."""
    case = {"event_id": "DEMO-001", "tenant_id": "demo", "product_id": "demo-pen", "presentation": "pen", "site_id": "demo-site",
            "excursion_start": "2026-01-02T10:00:00Z", "alert_received": "2026-01-02T10:01:00Z",
            "storage_instruction": "2-8 C", "measurements": {"min_c": 3, "max_c": 7}, "evidence": []}
    for kind in ("identity", "storage_spec", "telemetry", "sop", "stability"):
        case["evidence"].append({"id": "synthetic-" + kind, "kind": kind, "tenant_id": "demo", "product_id": "demo-pen", "site_id": "demo-site",
                                 "presentation": "pen", "approved": True, "approved_by": "fixture-author", "sha256": "a" * 64,
                                 "valid_from": "2025-01-01T00:00:00Z", "valid_to": None})
    return case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="evidence.sqlite")
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("demo")
    run = subs.add_parser("evaluate")
    run.add_argument("file")
    run.add_argument("--tenant", required=True)
    replay = subs.add_parser("replay")
    replay.add_argument("snapshot_id")
    replay.add_argument("--tenant", required=True)
    args = parser.parse_args()
    archive = Archive(args.db)
    try:
        if args.command == "replay":
            output = archive.replay(args.snapshot_id, args.tenant)
        else:
            if args.command == "demo":
                case, tenant = demo(), "demo"
            else:
                with open(args.file, encoding="utf-8") as stream:
                    case = json.load(stream)
                tenant = args.tenant
            key, result = archive.save(case, tenant)
            output = {"snapshot_id": key, "result": result}
            if args.command == "demo":
                output["replay"] = archive.replay(key, tenant)
        print(json.dumps(output, indent=2))
    finally:
        archive.close()


if __name__ == "__main__":
    main()
