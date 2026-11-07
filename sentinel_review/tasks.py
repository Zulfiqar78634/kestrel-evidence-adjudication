"""Resolution tasks: what is missing, which role must resolve it, and what evidence counts.

Tasks are derived deterministically from an assembled result. They carry a functional role,
never a named individual. They are initialized as OPEN: no transcription or cleared flag
can automatically bypass verified human review.
"""
from __future__ import annotations
from typing import Any
from .domain import ResolutionTask, normalized

STATUS_OPEN = "OPEN"
QA = "QA reviewer"
STABILITY = "QA / stability study owner"
DOCUMENTS = "Document control / QA"
SITE_QA = "Site QA"
DATA = "Platform data steward"

TASK_TEMPLATES: dict[str, tuple[str, str, str]] = {
    "SOURCE_CONTENT_NOT_VERIFIED": (
        DOCUMENTS,
        "The original source documents (study reports, SOPs, annexures), retrieved with a content hash.",
        "Each fact used is bound to a retrieved document version and page. An index row alone does not count.",
    ),
    "SITE_ACCEPTANCE_NOT_ESTABLISHED": (
        SITE_QA,
        "The SOP revision and annexure in force at the origin and destination sites on the event date, "
        "including any approved amendment.",
        "An authorised person records the acceptance limit that governs, with the document cited.",
    ),
    "BATCH_HISTORY_NOT_ESTABLISHED": (
        QA,
        "Batch identity and the complete prior-excursion history for that batch.",
        "History is attested complete, or QA records that it is unknown. Unknown is never treated as zero.",
    ),
    "PRODUCT_MAPPING_REQUIRES_APPROVAL": (
        QA,
        "Approval that the alert reference maps to this tenant's product, strength and presentation.",
        "The mapping is approved and recorded with the approver.",
    ),
    "PRODUCT_CANDIDATE_MISSING_OR_AMBIGUOUS": (
        QA,
        "Identification of the product: no candidate, or more than one, was found for the alert reference.",
        "One product is identified for this tenant and the choice is recorded with the approver.",
    ),
    "SOP_REVISION_OVERLAP": (
        DOCUMENTS,
        "A statement of which revision was in force on the event date, with the superseding document.",
        "One revision is confirmed. The highest revision number is not assumed to win.",
    ),
    "NO_DATED_SOP_CANDIDATE": (
        DOCUMENTS,
        "The SOP that was in force for this tenant on the event date.",
        "A dated SOP is located and cited, or QA records that none exists.",
    ),
    "EVENT_TIME_INVALID": (
        DATA,
        "Correct excursion start and alert receipt timestamps from the source system.",
        "Both timestamps are valid, in UTC, and the alert is not earlier than the excursion.",
    ),
    "EVENT_TIME_CONFLICT": (
        DATA,
        "Source confirmation of the excursion start and alert receipt times.",
        "The order of the two timestamps is explained or corrected at the source.",
    ),
    "MEASUREMENTS_INVALID_OR_MISSING": (
        DATA,
        "The raw temperature series for the excursion window from the logger vendor system.",
        "Minimum and maximum are re-derived from a complete series. A missing value is never read as safe.",
    ),
    "BULLETIN_APPLICABILITY_AND_SENSITIVITY_REQUIRE_REVIEW": (
        QA,
        "Whether the logger-firmware bulletin applies to this device and date, and how sensitive the "
        "outcome is to an under-reading of up to the bulletin's stated bound.",
        "QA records applicability and sensitivity. The bound is treated as uncertainty, not an exact correction.",
    ),
    "STUDY_APPLICABILITY_VERIFICATION": (
        STABILITY,
        "The original study report, confirming product, strength, presentation and permitted excursion.",
        "Applicability is approved by an authorised person. This index row alone is not approval.",
    ),
    "STUDY_REJECTION_CONFIRMATION": (
        STABILITY,
        "Confirmation that the study should be excluded, or the document showing that it applies.",
        "The listed rejection reasons are confirmed or overturned, with a document cited.",
    ),
    "ALLOWANCE_WORDING_RELATIONSHIP": (
        STABILITY,
        "A written statement of how the product master allowance and the study allowance relate "
        "(per excursion, repeated and cumulative).",
        "QA states the governing relationship. No combined rule is inferred by this tool.",
    ),
}

SHEETS = {"product": "02_Product_Master", "study": "06_Stability_Index", "sop": "05_SOP_Index"}


def _src(candidate: dict[str, Any]) -> dict[str, Any]:
    return {"sheet": candidate["sheet"], "row": candidate["row"]}


def _sources(reason: str, event_src: dict[str, Any], result: dict[str, Any]) -> list[dict[str, Any]]:
    products = [_src(c) for c in result["product_candidates"]]
    studies = [_src(c["source"]) for c in result["study_candidates"]]
    sops = [_src(c) for c in result["sop_candidates"]]
    picked = {
        "SOURCE_CONTENT_NOT_VERIFIED": studies + sops,
        "SITE_ACCEPTANCE_NOT_ESTABLISHED": sops,
        "PRODUCT_MAPPING_REQUIRES_APPROVAL": products,
        "SOP_REVISION_OVERLAP": [s for s in sops if s["sheet"] == SHEETS["sop"]],
    }.get(reason, [])
    unique = {(s["sheet"], s["row"]): s for s in [event_src] + picked}
    return [unique[k] for k in sorted(unique)]


def _task(event_id: str, reason: str, sources: list[dict[str, Any]], detail: str = "", ref: str = "") -> dict[str, Any]:
    role, evidence, criterion = TASK_TEMPLATES[reason]
    suffix = ":" + ref if ref else ""
    task_obj = ResolutionTask(
        id=f"{event_id}:{reason}{suffix}",
        reason=reason,
        role=role,
        evidence_requested=evidence,
        completion_criterion=criterion,
        sources=sources,
        status=STATUS_OPEN,
        detail=detail,
    )
    return task_obj.to_dict()


def derive_tasks(event_src: dict[str, Any], result: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive deterministic, role-assigned resolution tasks for all blockers and study candidates."""
    event_id = result["event_id"]
    tasks = [_task(event_id, reason, _sources(reason, event_src, result)) for reason in result["blockers"]]
    master_text = ""
    if result["product_candidates"]:
        master_text = normalized(result["product_candidates"][0]["values"].get("permitted_excursion_text"))
    for candidate in result["study_candidates"]:
        study = candidate["source"]
        ref = f"{study['values'].get('study_ref')}@{study['row']}"
        sources = [event_src] + [_src(c) for c in result["product_candidates"]] + [_src(study)]
        rejections = candidate["discovery_rejections"]
        if rejections:
            tasks.append(_task(event_id, "STUDY_REJECTION_CONFIRMATION", sources, ", ".join(rejections), ref))
            continue
        tasks.append(_task(event_id, "STUDY_APPLICABILITY_VERIFICATION", sources, "", ref))
        study_text = normalized(study["values"].get("permitted_excursion_text"))
        if master_text and study_text and master_text != study_text:
            detail = (
                f"Product master: {result['product_candidates'][0]['values'].get('permitted_excursion_text')!r}. "
                f"Study: {study['values'].get('permitted_excursion_text')!r}."
            )
            tasks.append(_task(event_id, "ALLOWANCE_WORDING_RELATIONSHIP", sources, detail, ref))
    return sorted(tasks, key=lambda t: t["id"])
