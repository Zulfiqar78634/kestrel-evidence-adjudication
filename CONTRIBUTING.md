# Contributing

## Before you change anything
1. Read the README sections "How the code is organised" and "What it does not do".
2. Write a failing test first, run it, and keep the failure output.
3. Make the change, then run the gates from the README.

## Rules for this repository
- Never commit the original brief, the workbook, generated real-case JSON, HTML or SQLite files.
- Historical labels (triage, final disposition, the misnamed `rules_engine_recommendation` column) must never become evidence that a case is safe or can be closed.
- Missing, malformed or nonfinite evidence must stay visible as a blocker. It must not turn into a safe default.
- Do not invent clinical limits, approvals, batch history or regulatory rules. Raise a question for Kestrel instead.
- A discovered candidate is not an approved authority. Keep that wording in code, tests and docs.
- Keep "implemented", "designed" and "tested" apart in every claim. State what was actually run.

## Commit hygiene
One focused change per commit. The message says what changed and why. Do not combine a feature with unrelated clean-up.
