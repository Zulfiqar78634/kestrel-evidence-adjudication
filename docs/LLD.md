# B2. Low-level design

## Code boundaries (implemented)
- `domain.py`: SourceRow, TenantScope, hashing, GTIN and timestamp parsing. No I/O.
- `ports.py`: `SourceCatalog` and `EvidenceRepository` protocols. A catalog must raise ValueError for an unknown sheet.
- `workbook.py`: reads the private workbook into SourceRow tuples. An empty sheet raises ValueError.
- `assembly.py`: `assemble` (candidates, rejections, blockers, tasks), `snapshot`, `FrozenCatalog`.
- `tasks.py`: `derive_tasks`. See `RESOLUTION-TASKS.md`.
- `storage.py`: SQLiteRepository (bundles, obligations).
- `service.py`: `ReviewService.review` and `replay`, depending only on ports.
- `cli.py`: transport only.
- `demo.py`: builds the synthetic workbook.

## Package result (implemented)
`assemble` returns event_id, tenant, version, status (always BLOCKED), final_disposition (always null), measurement state, sorted blockers, product, study and SOP candidates with sheet and row, overlapping doc ids, `resolution_tasks` and `historical_classification_used_as_proof=false`.

Blockers: SOURCE_CONTENT_NOT_VERIFIED, SITE_ACCEPTANCE_NOT_ESTABLISHED, BATCH_HISTORY_NOT_ESTABLISHED (always); PRODUCT_MAPPING_REQUIRES_APPROVAL or PRODUCT_CANDIDATE_MISSING_OR_AMBIGUOUS; SOP_REVISION_OVERLAP; NO_DATED_SOP_CANDIDATE; EVENT_TIME_INVALID or EVENT_TIME_CONFLICT; MEASUREMENTS_INVALID_OR_MISSING; BULLETIN_APPLICABILITY_AND_SENSITIVITY_REQUIRE_REVIEW (firmware TT-2.14.3).

Study candidates carry `discovery_rejections`, `authority=UNVERIFIED` and `strength_and_effective_date=NOT_ESTABLISHED`. An empty rejection list is not approval.

## Discovery rules (implemented, lexical)
Product: same tenant, and the alert reference equals a GTIN (normalised), SKU, brand, generic name or legacy code. Study: same tenant, and it is cited by the master, or shares the generic name or a brand word. Rejections: PRESENTATION_CONFLICT (the brand has the whole word "pen" or "solojet" and the study text has the whole word "vial"), NOT_EXCURSION_STUDY, NOT_FULLY_READABLE, ALLOWANCE_NOT_INDEXED. SOP: same tenant, "excursion" in the title, and the event date inside the effective dates. A date-only end date counts as the whole day (discovery assumption only).

## Persistence (implemented)
`bundles(tenant, id, payload)`, key (tenant, id). The id is the SHA-256 of the canonical payload. Identical content saves once. Reading verifies the hash.

`obligations(tenant, event_id, reportability, due_utc, state, basis)`. An imported Y with a positive window gives alert time plus window. Anything else is APPLICABILITY_UNVERIFIED; blank is UNKNOWN. INSERT OR IGNORE means a later source correction does not update the row (open item O2 in `REVIEW.md`).

## Snapshot and replay (implemented)
The snapshot holds the alert row and only the rows the result used: the product candidate, the SOP candidates and the study candidates. Replay verifies the hash and version, rebuilds a FrozenCatalog from those rows, runs assembly again and compares the full result. The workbook is not needed. On the 420-event sample this gives identical results and bundles 73% smaller than storing whole tenant tables.

Hashes detect edits to stored records. They do not stop someone who rewrites record and hash together, and they do not prove the source facts. The version string is a label, not an archived executable.

## CLI contract (implemented)
`review` needs `--tenant`, or `--all-tenants` for an operator run. Exit 0 on success. On PermissionError, LookupError, ValueError or KeyError it prints `{"error", "message"}` to stderr and exits 2. Argument errors also exit 2.

## Target design (not built)
Case states: RECEIVED, ASSEMBLING, BLOCKED or READY_FOR_REVIEW, PENDING_SECOND_SIGNATURE where the tenant requires it, DISPOSITION_SIGNED, then a linked REASSESSMENT for new evidence. Obligations: APPLICABILITY_PENDING, REQUIRED, SUBMITTING, SUBMITTED, ACKNOWLEDGED, with RETRY and ESCALATED. Signing a disposition must never remove an obligation.

Schema sketch: source_version, entity_link (with negative links), case_revision, evidence_binding, resolution_task, exposure_entry (unique per source event), notification_obligation, approval, outbox. Every key includes tenant.

API sketch: POST /v1/cases with an Idempotency-Key (202; same key with a different payload is 409); GET revision (404 for both missing and unauthorised); POST approvals with revision and evidence hash (403, 409, 422, 202 waiting for a second signer); independent GET notification-obligations; POST reassessments.

Concurrency: approval locks the revision and compares the evidence hash the signer viewed. Batch exposure uses a unique source-event key so a retry cannot spend an allowance twice.

## Known limits
Inputs are plain dictionaries with no full schema. Tenant arguments are trusted local input. Discovery is word-overlap and carries no authority. No facility, carrier or alias resolution. See `REVIEW.md` for the full open list.
