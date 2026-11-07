# Kestrel Evidence Adjudication

When a medicine shipment's thermometer goes out of range, a qualified person has to decide what happens to it. Most of their time goes on finding and checking the facts. This tool does that first step: for each alert it finds candidate product, study and SOP records, says why each is or is not usable, and lists what a person still has to confirm. It saves the result so it can be replayed. It never releases, destroys or signs product and is not a validated clinical system.

New here? Read [docs/START-HERE.md](docs/START-HERE.md).

## How one case flows

```mermaid
flowchart LR
  A[Alert row] --> B[Tenant check]
  B --> C[Save notification obligation]
  C --> D[Find product, study, SOP candidates]
  D --> E[Add rejection reasons and blockers]
  E --> F[Create OPEN resolution tasks]
  F --> G[Save used rows and hash]
  G --> H[Replay from saved rows]
  E --> I[Result BLOCKED, no disposition]
```

The obligation is saved before assembly so a later failure cannot erase it. Every result is BLOCKED because source documents, approvals and batch history are not available to this tool (see [ADR 0001](docs/adr/0001-blocked-by-default.md)).

## Try it locally (no private data needed)
```sh
git clone https://github.com/Zulfiqar78634/kestrel-evidence-adjudication
cd kestrel-evidence-adjudication
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v          # 48 pass, 1 skipped (needs the private workbook)
python -m sentinel_review.demo demo.xlsx          # builds a SYNTHETIC workbook
sentinel-review --db demo.sqlite review demo.xlsx --event DEMO-1 --tenant T-DEMO-A --out demo-out.json
sentinel-review --db demo.sqlite replay BUNDLE_ID --tenant T-DEMO-A     # BUNDLE_ID is in demo-out.json
sentinel-review --db demo.sqlite obligations --tenant T-DEMO-B
```
`make test`, `make demo` and `make check` run the same commands where `make` is installed. On Windows use the `python -m` forms. `review` needs `--tenant`, or `--all-tenants` for an operator run. Failures print a JSON error to stderr and exit with code 2.

With the real workbook (kept outside this repo):
```sh
KCCS_WORKBOOK=/private/KCCS_Sentinel_Reference_Data_Pack.xlsx python -m unittest discover -s tests -v
sentinel-review --db run.sqlite review /private/KCCS_Sentinel_Reference_Data_Pack.xlsx --event EXC-107133 --tenant T-KAVERI --out case.json
```
Do not commit `case.json` or SQLite files; they contain real case data.

## Documentation map
| Kind | Page |
|---|---|
| Explanation | [START-HERE](docs/START-HERE.md), [POSITION](docs/POSITION.md), [HLD](docs/HLD.md), [ADR 0001](docs/adr/0001-blocked-by-default.md) |
| Tutorial / how-to | [START-HERE](docs/START-HERE.md), [INTERVIEW](docs/INTERVIEW.md) (demo script) |
| Reference | [LLD](docs/LLD.md), [RESOLUTION-TASKS](docs/RESOLUTION-TASKS.md) |
| Honest status | [REVIEW](docs/REVIEW.md) (known weaknesses), [VALIDATION](docs/VALIDATION.md) (what was run), [AI-WORKING-LOG](docs/AI-WORKING-LOG.md) |

## How the code is organised

| Module | Role | Depends on |
|---|---|---|
| `sentinel_review/domain.py` | Pure helpers: hashing, parsing, tenant scope | nothing |
| `sentinel_review/ports.py` | Interfaces: `SourceCatalog`, `EvidenceRepository` | domain |
| `sentinel_review/workbook.py` | Adapter: reads the workbook | domain, openpyxl |
| `sentinel_review/tasks.py` | Resolution tasks per blocker | domain |
| `sentinel_review/assembly.py` | Candidate discovery, rejection reasons, blockers | domain, ports, tasks |
| `sentinel_review/storage.py` | Adapter: SQLite bundles and obligations | domain |
| `sentinel_review/service.py` | Use cases: `review`, `replay` | assembly, ports |
| `sentinel_review/cli.py` | Local operator CLI | all of the above |
| `sentinel_review/demo.py` | Builds the synthetic demo workbook | openpyxl |

Service and assembly code depend on the interfaces in `ports.py`, not on SQLite or the workbook, so tests can run them on in-memory data. `kestrel.py` with `tests/test_kernel.py` and `tests/test_integration.py` is an earlier single-file synthetic kernel (v0.1.0), kept for history.

## Quality gates
```sh
ruff check sentinel_review     # blocking in CI
mypy                           # informational in CI until typed models land (Step 2)
coverage run -m unittest discover -s tests && coverage report
```

## What it does not do
No authenticated API or roles, no qualified or dual signing, no source-document verification, no approved identity mapping, no batch or once-only ledger, no calendar or notification delivery, no immutable archive, no way to close a task, no measured scale. The full list of known weaknesses is in [docs/REVIEW.md](docs/REVIEW.md).

## Roadmap

| Step | Work | Status |
|---|---|---|
| 1 | Quality gates (ruff, mypy, coverage) and README | Committed; CI result not observed |
| 2 | Typed domain models in place of plain dictionaries; make mypy blocking | Not started |
| 3 | Resolution tasks, synthetic demo workbook, local-test tooling | Committed; CI result not observed |
| 4 | Input validation and structured CLI errors | Partly done (clean CLI errors, explicit tenant); input validation not started |
| 5 | Authenticated API with tenant from the token; task closure with approved evidence | Not started |
| 6 | Postgres adapter, migrations and shared adapter contract tests | Not started |
| 7 | ADRs, diagrams, runbook; docs kept in step with behaviour | Partly done |
| 8 | Retire or move the legacy single-file kernel | Not started |

Each step is a separate commit, written test-first, and not marked done until its gate has run.

## Verification status (v0.3.1)
Last executed locally: 49 tests (all pass with the private workbook; 48 pass and 1 is skipped without it), 420 of 420 events replayed identically with 0 results changed by the review fixes, and an installed console command ran end to end. Not verified: the remote CI result, ruff and mypy results, a combined run with the legacy tests, and any clinical, security or scale property.
