# B2. Low-level design

## Code boundaries (implemented)
- `domain.py`: SourceRow, TenantScope, deterministic serialization/hash, GTIN and timestamp normalization. No I/O.
- `ports.py`: SourceCatalog and EvidenceRepository protocols.
- `workbook.py`: reads the private workbook into SourceRow tuples.
- `assembly.py`: pure `assemble` (candidates, rejections, blockers), `snapshot`, `FrozenCatalog` for replay.
- `storage.py`: SQLiteRepository (bundles, obligations).
- `service.py`: `ReviewService.review` and `replay`, depending only on ports.
- `cli.py`: transport only.
The boundaries let a database-backed catalog or repository replace the adapters without touching assembly. This is a structural claim exercised with in-memory, frozen and workbook catalogs; it is not a general proof of design quality.

## Package result (implemented)
`assemble` returns event_id, tenant, version, status (always BLOCKED), final_disposition (always null), measurement state, sorted blockers, product/study/SOP candidates with sheet and row, overlapping doc ids and `historical_classification_used_as_proof=false`.

Blockers: SOURCE_CONTENT_NOT_VERIFIED, SITE_ACCEPTANCE_NOT_ESTABLISHED, BATCH_HISTORY_NOT_ESTABLISHED (always), PRODUCT_MAPPING_REQUIRES_APPROVAL or PRODUCT_CANDIDATE_MISSING_OR_AMBIGUOUS, SOP_REVISION_OVERLAP, NO_DATED_SOP_CANDIDATE, EVENT_TIME_INVALID/CONFLICT, MEASUREMENTS_INVALID_OR_MISSING, BULLETIN_APPLICABILITY_AND_SENSITIVITY_REQUIRE_REVIEW (firmware TT-2.14.3).

Study candidates carry discovery_rejections (PRESENTATION_CONFLICT, NOT_EXCURSION_STUDY, NOT_FULLY_READABLE, ALLOWANCE_NOT_INDEXED), authority=UNVERIFIED and strength_and_effective_date=NOT_ESTABLISHED. An empty rejection list is not approval. Product text never substitutes for study authority.

## Persistence (implemented)
`bundles(tenant, id, payload)` with primary key (tenant, id); id is the SHA-256 of the canonical payload; INSERT OR IGNORE makes identical content idempotent; read verifies the hash. `obligations(tenant, event_id, reportability, due_utc, state, basis)`; imported Y with a positive window gives alert time plus window, anything else is APPLICABILITY_UNVERIFIED; blank is UNKNOWN. A later source correction would need a versioned obligation; current INSERT OR IGNORE does not do that.

## Replay (implemented)
The payload stores the event row plus same-tenant product, SOP and stability rows. Replay verifies the hash and version, rebuilds a FrozenCatalog, re-runs assembly and compares the full result. The workbook is not needed. Hashes detect edits to stored records, not an administrator who rewrites record and hash together, and not wrong source facts. The version string is a label, not an archived executable.

## Target case states (not built)
RECEIVED -> ASSEMBLING -> BLOCKED | READY_FOR_REVIEW -> PENDING_SECOND_SIGNATURE (if the tenant requires it) -> DISPOSITION_SIGNED -> REASSESSMENT (linked, never in place). Only BLOCKED packages exist in v0.2.0.
Target obligation: APPLICABILITY_PENDING -> REQUIRED -> SUBMITTING -> SUBMITTED -> ACKNOWLEDGED, with RETRY and ESCALATED. Signing a disposition has no power to remove an obligation; NOT_REQUIRED needs qualified evidence, not an imported flag.

## Target schema sketch (not migrated)
source_version(tenant, source_id, version, valid_from, valid_to, recorded_at, content_hash, object_key); entity_link(tenant, kind, left_ref, right_entity, relation, approval_state, approved_by, intervals) including negative links; case_revision(tenant, case_id, revision, state, manifest_hash, row_version); evidence_binding(case_id, revision, source_version, claim, source_span, authority_state); resolution_task(owner, reason, state); exposure_entry(tenant, batch_id, source_event unique); notification_obligation(deadline, calendar_version, state, ack_ref, row_version); approval(role, principal, evidence_hash, meaning); outbox. Composite keys always include tenant.

## Target API (not exposed)
POST /v1/cases with Idempotency-Key (202; same key with different payload is 409). GET /v1/cases/{id}/revisions/{n} (404 for both unauthorized and absent). POST /v1/cases/{id}/approvals with revision and evidence_hash (403 role, 409 stale evidence, 422 unresolved authority, 202 awaiting second signer). Independent GET /v1/notification-obligations. POST /v1/reassessments for new evidence.

## Concurrency (target)
Approval locks the revision and compares the evidence hash the signer viewed. Batch exposure consumption locks tenant and batch with a unique source-event key so a retry cannot double-spend an allowance. The second signer must be independent and bound to the same revision. Store source objects first and reference only verified durable objects.

## Known limits in the code
Inputs are plain dictionaries without a full schema. CLI errors surface as tracebacks. Tenant arguments are trusted local input. Candidate discovery is lexical and may over- or under-include; that is why nothing it finds carries authority. No facility, carrier or alias resolution is performed in v0.2.0.
