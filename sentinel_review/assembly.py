"""Evidence candidate assembly. Discovery and blockers only: NOT clinical policy or approval."""
from datetime import datetime
from .domain import SourceRow, TenantScope, finite, gtin, normalized, utc
from .ports import SourceCatalog

VERSION = "0.2.0"
IDENTITY_FIELDS = ("internal_sku", "brand_as_labelled", "generic_inn", "legacy_code")


def product_matches(event: SourceRow, product: SourceRow) -> bool:
    ref = event.values.get("product_ref_as_received")
    if not normalized(ref):
        return False
    return (bool(gtin(ref)) and gtin(ref) == gtin(product.values.get("gtin"))) or any(
        normalized(ref) == normalized(product.values.get(f)) for f in IDENTITY_FIELDS
        if normalized(product.values.get(f)))


def assemble(catalog: SourceCatalog, event: SourceRow, tenant: str) -> dict:
    TenantScope(tenant).check(event)
    blockers = ["SOURCE_CONTENT_NOT_VERIFIED", "SITE_ACCEPTANCE_NOT_ESTABLISHED", "BATCH_HISTORY_NOT_ESTABLISHED"]
    try:
        start, alert = utc(event.values.get("excursion_start_utc")), utc(event.values.get("alert_ts_utc"))
        if alert < start:
            blockers.append("EVENT_TIME_CONFLICT")
    except (ValueError, TypeError):
        start = None
        blockers.append("EVENT_TIME_INVALID")
    try:
        lo, hi = finite(event.values.get("min_temp_c")), finite(event.values.get("max_temp_c"))
        if lo > hi:
            raise ValueError("reversed extrema")
        measurement = "SUMMARY_PRESENT_NOT_SERIES_VERIFIED"
    except (ValueError, TypeError):
        measurement = "UNKNOWN"
        blockers.append("MEASUREMENTS_INVALID_OR_MISSING")
    products = [p for p in catalog.rows("02_Product_Master")
                if p.values.get("tenant_code") == tenant and product_matches(event, p)]
    blockers.append("PRODUCT_MAPPING_REQUIRES_APPROVAL" if len(products) == 1
                    else "PRODUCT_CANDIDATE_MISSING_OR_AMBIGUOUS")
    studies = []
    if len(products) == 1:
        product = products[0].values
        brand, molecule = normalized(product.get("brand_as_labelled")), normalized(product.get("generic_inn"))
        tokens = set(brand.split())
        for study in catalog.rows("06_Stability_Index"):
            row = study.values
            if row.get("tenant_code") != tenant:
                continue
            text = normalized(row.get("product_text_as_written"))
            cited = row.get("study_ref") == product.get("stability_study_ref")
            # Lexical discovery only: never establishes equivalence, strength or authority.
            if not (cited or (molecule and molecule in text) or (tokens and tokens & set(text.split()))):
                continue
            reasons = []
            if ("pen" in brand or "solojet" in brand) and "vial" in text:
                reasons.append("PRESENTATION_CONFLICT")
            if "excursion" not in normalized(row.get("study_type")):
                reasons.append("NOT_EXCURSION_STUDY")
            if normalized(row.get("readable")) != "y":
                reasons.append("NOT_FULLY_READABLE")
            if not row.get("permitted_excursion_text"):
                reasons.append("ALLOWANCE_NOT_INDEXED")
            studies.append({"source": study.snapshot(), "cited_by_master": cited,
                            "discovery_rejections": reasons, "authority": "UNVERIFIED",
                            "strength_and_effective_date": "NOT_ESTABLISHED"})
    sops = []
    for sop in catalog.rows("05_SOP_Index"):
        row = sop.values
        if row.get("tenant_code") != tenant or "excursion" not in normalized(row.get("title")):
            continue
        try:
            begins = utc(row["effective_from"])
            valid = start is not None and begins <= start
            if valid and row.get("effective_to"):
                end = utc(row["effective_to"])
                # Date-only end treated as inclusive calendar day: discovery assumption only.
                valid = start.date() <= end.date() if end.time() == datetime.min.time() else start <= end
        except (ValueError, TypeError, KeyError):
            valid = False
        if valid:
            sops.append(sop.snapshot())
    by_doc = {}
    for sop in sops:
        by_doc.setdefault(sop["values"].get("doc_id"), []).append(sop)
    overlaps = [key for key, rows in by_doc.items() if len(rows) > 1]
    if overlaps:
        blockers.append("SOP_REVISION_OVERLAP")
    if not sops:
        blockers.append("NO_DATED_SOP_CANDIDATE")
    if event.values.get("logger_fw") == "TT-2.14.3":
        blockers.append("BULLETIN_APPLICABILITY_AND_SENSITIVITY_REQUIRE_REVIEW")
    return {"event_id": event.values.get("event_id"), "tenant": tenant, "version": VERSION,
            "status": "BLOCKED", "final_disposition": None, "measurement": measurement,
            "blockers": sorted(set(blockers)), "product_candidates": [p.snapshot() for p in products],
            "study_candidates": studies, "sop_candidates": sops, "overlapping_doc_ids": overlaps,
            "historical_classification_used_as_proof": False}


def snapshot(catalog: SourceCatalog, event: SourceRow, tenant: str) -> dict:
    TenantScope(tenant).check(event)
    return {"event": event.snapshot(), "tables": {
        name: [r.snapshot() for r in catalog.rows(name) if r.values.get("tenant_code") == tenant]
        for name in ("02_Product_Master", "05_SOP_Index", "06_Stability_Index")}}


class FrozenCatalog:
    """Replay source built only from captured, tenant-scoped rows."""
    def __init__(self, captured: dict):
        self.tables = {name: tuple(SourceRow(r["sheet"], r["row"], r["values"]) for r in rows)
                       for name, rows in captured["tables"].items()}

    def rows(self, name):
        return self.tables[name]
