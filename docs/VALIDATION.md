# C. Validation: what was actually run

Environment: Python 3.12.8, openpyxl 3.1.5, the original workbook supplied privately.

## Executed
- `python -m unittest discover -s tests -v` on the new package with the private workbook set: 19 tests, all passed (18 synthetic plus 1 original-workbook test).
- Same run without the workbook: 19 run, 1 skipped, OK.
- All 420 workbook events assembled and saved, then replayed from stored inputs: 420 of 420 identical.
- CLI `review` for EXC-107133 (T-KAVERI) then CLI `replay` of the saved bundle: both exit 0, identical=true.

## Observed on the 420-event extract
Every event is BLOCKED (by design: source content, site acceptance and batch history cannot be established from index rows). Blocker counts: BATCH_HISTORY_NOT_ESTABLISHED 420; SITE_ACCEPTANCE_NOT_ESTABLISHED 420; SOURCE_CONTENT_NOT_VERIFIED 420; PRODUCT_MAPPING_REQUIRES_APPROVAL 297; PRODUCT_CANDIDATE_MISSING_OR_AMBIGUOUS 123; NO_DATED_SOP_CANDIDATE 164; BULLETIN_APPLICABILITY_AND_SENSITIVITY_REQUIRE_REVIEW 91; SOP_REVISION_OVERLAP 13. The sample is stratified, so these are not production rates (workbook 00_README).

EXC-107133: product candidate = 02 row 57; study candidates STB-2738 (row 105, no discovery rejection, still unverified), STB-4400 (row 106), STB-3312 (row 107), STB-3584 (row 108, presentation/type/readability/allowance issues); SOP candidates rows 203-204 overlapping. Status BLOCKED, no disposition.

## Not executed or not established
Remote GitHub CI for this commit; the legacy 33 tests together with the new ones in one local run (they passed earlier on the earlier commit); package installation; Docker; coverage; fuzz, property, load, concurrency, crash-recovery and restore tests; authentication, roles and signing; source-document verification; legal notification calendars and delivery; any clinical correctness or scale claim.

## Interpretation limits
420 of 420 blocked is not an accuracy result. Replay shows the same inputs reproduce the same package, not that the inputs are true. Passing tests do not demonstrate production readiness.
