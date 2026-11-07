# Kestrel Evidence Adjudication

Independent, offline evidence-readiness kernel. Python 3.10+, standard library only. No clinical or production certification.

## Run
```sh
python -m unittest discover -s tests -v
python kestrel.py --db demo.sqlite demo
python kestrel.py --db demo.sqlite evaluate case.json --tenant demo
python kestrel.py --db demo.sqlite replay SNAPSHOT_ID --tenant demo
```
The demo creates synthetic input, evaluates it, saves a snapshot and verifies identical replay. See `demo()` for the input schema.

## What works
Explicit unknown measurements; strict/inclusive and one/two-sided limits; Decimal comparisons; under-reading uncertainty envelope; tenant/product/site/presentation evidence-envelope checks; dated applicability; unresolved exposure policies; deterministic results; atomic SQLite snapshots and scoped replay. Historical triage does not authorize closure.

## Output boundaries
EVIDENCE_INCOMPLETE means unresolved evidence. CLOSURE_CANDIDATE is not executed closure or product release. READY_FOR_QA is not proof of clinical safety. All product dispositions remain human-required.

## Trust and limitations
Approved booleans are trusted-input assertions, not authenticated approvals. Source hashes are format-checked, not verified against original bytes; demo hashes are placeholders. Caller tenant is local scope, not authentication. The kernel does not prove supplied measurements or instructions came from the referenced sources. No authoritative identity registry, original-workbook integration, raw-series completeness, batch ledger, legal notification service, qualified signing, immutable archive or load-tested deployment is implemented. Do not expose this CLI as a multi-user service.

## Actual validation
Locally executed on Python 3.12.8: 23 tests passed; CLI demo saved and replayed identically. Other Python versions, GitHub CI, Docker, original-data evaluation and load testing have not been verified.

## Delivery status
First runnable slice, not the complete assignment submission. Design/report/operations/AI-log documents are supplied in the accompanying chat ZIP and are not yet committed here. No confidential PDF/workbook or third-party implementation is published.
