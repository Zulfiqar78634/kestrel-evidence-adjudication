# C. Validation: what was actually run

Environment: Python 3.12.8, openpyxl 3.1.5, GNU Make 4.4.1, the original workbook supplied privately. Numbers are for version 0.3.1.

## Executed for the v0.3.1 review
- The pushed code (commit 216a09c) was rebuilt and its 37 tests passed.
- Twelve new tests were written first. Eight failed because of real defects (word match, empty sheet, catalog error type, snapshot size x2, missing refusal, error output x2 counted as separate checks in the run). A ninth, the version check, failed only because my scratch folder had no pyproject.toml; it passed once the file was there. Three guard tests passed from the start.
- After the fixes: 49 tests. With the private workbook set, all passed. Without it, 48 passed and 1 was skipped.
- All 420 workbook events were assembled, saved and replayed from saved rows: 420 of 420 identical. Compared with the pushed code, 0 results changed.
- Saved bundles for those 420 events: 11.56 MB before, 3.15 MB after (average 27.5 KB to 7.5 KB).
- A package build succeeded. The installed `sentinel-review` command ran review (exit 0), replay (exit 0), a wrong-tenant replay (exit 2, JSON error) and a review without a tenant (exit 2).
- A check of line length and unused imports on `sentinel_review/` found nothing.
- Earlier, for v0.3.0: 2,624 resolution tasks across the 420 events, every blocker had a task, every task was OPEN with at least one source, and EXC-107133 had 10 tasks.

## Observed on the 420-event extract
Every event is BLOCKED by design. The sample is stratified, so no count is a production rate (workbook 00_README). 170 events have an allowance-wording task.

## Not executed or not established
The remote CI result for this commit. `ruff`, `mypy` and `coverage`. A single combined run of the legacy tests with the new ones. Docker. Fuzz, property, load, concurrency, crash-recovery and restore tests. Authentication, roles and signing. Source-document verification. Legal notification calendars and delivery. Any clinical, security or scale claim.

## Interpretation limits
420 of 420 blocked is not an accuracy result. Replay shows the same saved rows give the same package, not that the rows are true. Passing tests do not show production readiness.
