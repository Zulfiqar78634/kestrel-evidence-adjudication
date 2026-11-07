# C. Validation: what was actually run

Environment: Python 3.12.8, openpyxl 3.1.5, GNU Make 4.4.1, the original workbook supplied privately. Numbers are for version 0.3.0.

## Executed
- Baseline before the change: the existing 19 tests passed (1 skipped without the workbook).
- New tests written first and run before the code existed: they failed because `sentinel_review.tasks` and `sentinel_review.demo` were missing.
- After implementation, `python -m unittest discover -s tests`: 37 tests. With the private workbook set, all passed. Without it, 36 passed and 1 was skipped.
- All 420 workbook events assembled, saved and replayed from stored inputs: 420 of 420 identical.
- Across those 420 events: 2,624 resolution tasks. Every blocker had a task, every task was OPEN, and every task had at least one source.
- EXC-107133: 10 tasks (see `RESOLUTION-TASKS.md`).
- A package build and install succeeded. The installed `sentinel-review` command ran review and replay end to end on the synthetic demo workbook (identical: true). `make -n check demo` ran without error.
- A check of line length and unused imports on `sentinel_review/` found nothing over 120 characters and no unused imports.

## Observed on the 420-event extract
Every event is BLOCKED by design. The sample is stratified, so no count here is a production rate (workbook 00_README). 170 events have an allowance-wording task because the product master and a non-rejected study use different wording; that counts text differences, not confirmed conflicts.

## Not executed or not established
The remote CI result for this commit. `ruff`, `mypy` and `coverage` (not installed where tests were run). A single combined run of the legacy tests with the new ones. Docker. Fuzz, property, load, concurrency, crash-recovery and restore tests. Authentication, roles and signing. Source-document verification. Legal notification calendars and delivery. Any clinical correctness, security or scale claim.

## Interpretation limits
420 of 420 blocked is not an accuracy result. Replay shows the same inputs give the same package, not that the inputs are true. Passing tests do not demonstrate production readiness.
