# Kestrel Evidence Adjudication

Evidence-first case-study submission for Kestrel's "The Adjudication Problem". It assembles reviewer-ready evidence packages from the supplied workbook, keeps unresolved authority explicit, and reproduces each package from captured inputs. It never releases, destroys or signs product and is not a validated clinical system.

## Contents
- `sentinel_review/` (v0.2.0): modular slice. `domain` (pure helpers), `ports` (interfaces), `workbook` (adapter), `assembly` (candidates + blockers), `storage` (SQLite), `service` (use cases), `cli`.
- `kestrel.py` + `tests/test_kernel.py`, `tests/test_integration.py`: earlier single-file synthetic evidence-readiness kernel (v0.1.0), kept for history.
- `docs/POSITION.md` (A), `docs/HLD.md` + `docs/LLD.md` (B), `docs/VALIDATION.md` (C), `docs/AI-WORKING-LOG.md` (D).

## Run
```sh
python -m pip install -e .
python -m unittest discover -s tests -v
# Optional: enable the original-workbook test (the workbook is private and NOT in this repo)
KCCS_WORKBOOK=/private/KCCS_Sentinel_Reference_Data_Pack.xlsx python -m unittest discover -s tests -v
python -m sentinel_review.cli --db run.sqlite review /private/KCCS_Sentinel_Reference_Data_Pack.xlsx --event EXC-107133 --tenant T-KAVERI --out case.json
python -m sentinel_review.cli --db run.sqlite replay BUNDLE_ID --tenant T-KAVERI
python -m sentinel_review.cli --db run.sqlite obligations --tenant T-KAVERI
```
Without the workbook the original-data test is skipped. Do not commit generated `case.json` or SQLite files; they contain real case data.

## What it does today
Tenant-scoped product, study and SOP candidate discovery with workbook sheet/row provenance; explicit rejection reasons and blockers; historical triage never used as proof; imported reportability references admitted before assembly; captured-input snapshots, integrity check and replay without the workbook.

## What it does not do
No authenticated API or roles, no qualified or dual signing, no source-document verification, no approved identity mapping, no batch/once-only ledger, no calendar or notification delivery, no immutable archive, no measured scale. Every one of the 420 sample events ends BLOCKED by design. See `docs/VALIDATION.md` for what was and was not executed.
