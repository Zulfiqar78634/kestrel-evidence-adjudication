# Kestrel Evidence Adjudication

Evidence-first case-study submission for Kestrel's "The Adjudication Problem". It assembles reviewer-ready evidence packages from the supplied workbook, keeps unresolved authority explicit, and reproduces each package from captured inputs. It never releases, destroys or signs product and is not a validated clinical system.

## How the code is organised

| Module | Role | Depends on |
|---|---|---|
| `sentinel_review/domain.py` | Pure helpers: hashing, parsing, tenant scope | nothing |
| `sentinel_review/ports.py` | Interfaces: `SourceCatalog`, `EvidenceRepository` | domain |
| `sentinel_review/workbook.py` | Adapter: reads the private workbook | domain, openpyxl |
| `sentinel_review/assembly.py` | Candidate discovery, rejection reasons, blockers | domain, ports |
| `sentinel_review/storage.py` | Adapter: SQLite bundles and obligations | domain |
| `sentinel_review/service.py` | Use cases: `review`, `replay` | assembly, ports |
| `sentinel_review/cli.py` | Local operator CLI | all of the above |

The service and assembly code depend on the interfaces in `ports.py`, not on SQLite or the workbook. That is why the unit tests can run them on in-memory data.

`kestrel.py` with `tests/test_kernel.py` and `tests/test_integration.py` is an earlier single-file synthetic kernel (v0.1.0), kept for history. It is not part of the new package's design.

Documents: `docs/POSITION.md` (A), `docs/HLD.md` and `docs/LLD.md` (B), `docs/VALIDATION.md` (C), `docs/AI-WORKING-LOG.md` (D).

## Run
```sh
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
# Optional: enable the original-workbook test (the workbook is private and NOT in this repo)
KCCS_WORKBOOK=/private/KCCS_Sentinel_Reference_Data_Pack.xlsx python -m unittest discover -s tests -v
sentinel-review --db run.sqlite review /private/KCCS_Sentinel_Reference_Data_Pack.xlsx --event EXC-107133 --tenant T-KAVERI --out case.json
sentinel-review --db run.sqlite replay BUNDLE_ID --tenant T-KAVERI
sentinel-review --db run.sqlite obligations --tenant T-KAVERI
```
`python -m sentinel_review.cli` works the same as `sentinel-review`. Without the workbook the original-data test is skipped. Do not commit generated `case.json` or SQLite files; they contain real case data.

## Quality gates
```sh
ruff check sentinel_review     # blocking in CI
mypy                           # informational in CI until Step 2
coverage run -m unittest discover -s tests && coverage report
```
Coverage is reported but has no pass threshold yet. Configuration lives in `pyproject.toml`.

## What it does today
Tenant-scoped product, study and SOP candidate discovery with workbook sheet and row provenance; explicit rejection reasons and blockers; historical triage never used as proof; imported reportability references admitted before assembly; captured-input snapshots with an integrity check and replay without the workbook.

## What it does not do
No authenticated API or roles, no qualified or dual signing, no source-document verification, no approved identity mapping, no batch or once-only ledger, no calendar or notification delivery, no immutable archive, no measured scale. Every one of the 420 sample events ends BLOCKED by design. See `docs/VALIDATION.md` for what was and was not executed.

## Roadmap

| Step | Work | Status |
|---|---|---|
| 1 | Quality gates (ruff, mypy, coverage) and README | Committed; the first CI run for this commit has not been observed |
| 2 | Typed domain models in place of plain dictionaries; make mypy blocking | Not started |
| 3 | Resolution tasks: role, evidence requested and completion criterion per blocker | Not started |
| 4 | Input validation and structured CLI errors | Not started |
| 5 | Authenticated API with tenant taken from the token | Not started |
| 6 | Postgres adapter, migrations and shared adapter contract tests | Not started |
| 7 | ADRs, diagrams, runbook; keep docs in step with behaviour | Not started |
| 8 | Retire or move the legacy single-file kernel | Not started |

Each step is a separate commit, written test-first, and not marked done until its gate has run.

## Verification status
Last executed locally: 19 tests on the new package (18 synthetic and 1 against the private workbook), 420 of 420 events replayed identically, and a non-editable package build and install succeeded. Not verified: the remote CI result for the latest commit, ruff and mypy results, a combined run of the legacy and new tests, and any clinical, security or scale property.
