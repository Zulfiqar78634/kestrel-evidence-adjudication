# Kestrel Evidence Adjudication

Independent evidence-first case-study kernel. Runnable offline with synthetic data; Python 3.10+, standard library only. A bounded working slice, not a completed production platform.

## Quick start
```sh
git clone https://github.com/Zulfiqar78634/kestrel-evidence-adjudication
cd kestrel-evidence-adjudication
python -m unittest discover -s tests -v
python kestrel.py --db demo.sqlite demo
```
The demo evaluates a synthetic case, saves it and replays the snapshot. For JSON input schema see demo() in kestrel.py.
```sh
python kestrel.py --db demo.sqlite evaluate case.json --tenant demo
python kestrel.py --db demo.sqlite replay SNAPSHOT_ID --tenant demo
```

## Verified behavior
33 local tests passed on Python 3.12.8. Tests include real CLI subprocesses, persisted restart/replay, wrong-tenant denial, missing readings, time/applicability conflicts, strict/one-sided limits, uncertainty, input preservation and tampering. Details and limitations: [verification report](docs/verification.md).
A GitHub Actions matrix is supplied for Python 3.10-3.13; remote success must be checked separately.

## Decision boundary
EVIDENCE_INCOMPLETE: unresolved facts or authority.
CLOSURE_CANDIDATE: supplied envelopes pass and extrema are within bounds; not an executed closure.
READY_FOR_QA: evidence-envelope checks pass and the excursion requires human assessment.
No product release, destruction, notification or qualified signature is performed. Historical triage never authorizes closure.

## Explicit trust boundary
Approved booleans are input assertions. Hashes are format-checked, not verified against original source bytes. Synthetic hashes are placeholders. Caller tenant is local scope, not authenticated identity. No authoritative identity registry, complete schema validation, raw-series verification, original-workbook integration, batch ledger, notification/calendar service, qualified signing or immutable archive is implemented. Do not expose this CLI as an authenticated multi-user service.

## Submission status
This repository is not yet the complete requested assignment or a production-qualified implementation. Local tests do not establish clinical correctness or scale. Further architecture/report material was supplied separately in the conversation and is not yet published here. No confidential PDF/workbook or third-party source is included.
