# Executed verification report

## Baseline and identity
Reviewed GitHub main at 5e454113b425b4456163ac78241a52deb8fb02f1.
Reconstructed fetched source locally and verified Git blob identity before execution:
- kestrel.py: 486f67b9418599e7d8f0f846afb785d1b122d6af
- tests/test_kernel.py: 826bcb5b3a45bd998d1099369aa570111f962d68
No network cloning or dependency installation was used in the execution sandbox.

## Actual execution
Python 3.12.8; SQLite 3.46.1.
Command: python -m unittest discover -s tests -v
Observed: 33 tests passed; exit 0. Includes all 23 original tests and 10 new integration/negative tests.
Command: python -m compileall -q kestrel.py tests
Observed: exit 0.

## Added checks
CLI demo and replay in a separate process; denied cross-tenant replay; missing-measurement CLI evaluation; malformed JSON nonzero exit without success output; SQLite restart persistence; future/unapproved evidence; event ordering; unchanged input; reversed extrema.
Existing tests cover one-sided bounds, strict/inclusive boundaries, negative ranges, uncertain readings, invalid/missing extrema, identity scope, presentation/SOP ambiguity, interval endpoints, exposure flags, integrity and deterministic evaluation.

## Limits and failures not hidden
This is not comprehensive production qualification. The CLI currently emits Python tracebacks for invalid JSON and authorization failures; the tests establish nonzero failure/no success output, not polished error contracts. Tenant arguments and approved metadata are trusted local inputs, not authenticated authority. Source hashes are not verified against original bytes. Input schema validation remains incomplete. Snapshots are not immutable storage and version labels do not archive executable builds.

Not run: remote GitHub CI, other Python versions, Docker, original-workbook integration, coverage measurement, property/fuzz tests, load/storm/concurrency/restore qualification or deployment. CI is configured by this change, not claimed passing. No production safety, clinical accuracy or interview outcome is established.
