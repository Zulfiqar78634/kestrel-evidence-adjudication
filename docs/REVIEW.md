# Engineering review of this repository (v0.3.0 reviewed, v0.3.1 fixed)

Method: Google's code-review checklist (design, functionality, complexity, tests, naming, comments, style, documentation), a SOLID check, and measurements on the real 420-event workbook. Every finding below was reproduced before it was fixed.

**Verdict.** Qualified as a tested, demonstrable prototype slice. Not qualified as production, secure or clinical software.

## Found and fixed
| ID | Severity | Problem | Evidence | Fix |
|---|---|---|---|---|
| F1 | Medium (latent) | "pen" and "vial" were matched as substrings, so a brand like Penicillin counted as a pen and got a false PRESENTATION_CONFLICT. | Reproduced with a test. No real brand in the workbook contains "pen" as a substring, so no real result changed. | Whole-word match. |
| F2 | Low | An empty sheet crashed with a bare StopIteration. | Reproduced. | Clear ValueError naming the sheet. |
| F3 | Low | The replay catalog raised KeyError for an unknown sheet and the workbook catalog raised ValueError. | Reproduced. | Both raise ValueError. The rule is written in `ports.py`. |
| F4 | Medium | Each saved bundle held every row of the tenant's product, SOP and study tables. | 420 bundles: 11.56 MB, average 27.5 KB. | Keep only the rows the result used. Now 3.15 MB, average 7.5 KB (73% smaller). The 420 results and replays are unchanged. |
| F5 | Low | The version lived in three places and could drift. | Read the code. | A test fails if package, evaluator and pyproject disagree. |
| F6 | Medium | `review` without `--tenant` silently reviewed all 8 tenants. | Reproduced. | Refused unless `--all-tenants` is given. |
| F7 | Low | Failures printed Python tracebacks. | Reproduced. | One-line JSON error on stderr, exit code 2. |
| F8 | Docs | I had written that the allowance-wording task might over-flag on formatting. | Checked all 170: none differ only by punctuation or spacing. | Docs corrected: they are real wording differences, but still not proven conflicts. |

## Found and not fixed
| ID | Severity | Problem | Plan |
|---|---|---|---|
| O1 | High | No authentication. The tenant is a command-line argument, so isolation is scoping, not security. | Step 5 |
| O2 | High | Obligations use INSERT OR IGNORE. If the source later corrects a reportability flag, the old row stays. | Needs a versioned obligation |
| O3 | Medium | Candidate discovery is word-overlap. Common tokens can pull in unrelated studies, and exact-name matching can miss real ones. Nothing found carries authority, so this adds noise, not risk. | Step 5/6 |
| O4 | Medium | No way to complete a task. Deliberate until approvals and signers exist. | Step 5 |
| O5 | Medium | `ruff`, `mypy` and `coverage` have not been run by me, and I have not seen a CI result. | Check the Actions tab |
| O6 | Low | Results are plain dictionaries, so typos in keys are found only by tests. | Step 2 |
| O7 | Low | `cli.main()` parses, filters, runs and prints in one function. | Split during Step 2 or 4 |
| O8 | Low | The CLI calls `repository.obligations()`, which is on the SQLite class but not in the `EvidenceRepository` port. A second adapter would break it. | Add to the port |
| O9 | Low | Test files share helpers with `from test_review import ...`, which works under `unittest discover` only. | Move to a shared module |
| O10 | Low | SQLite is used in one process with no timeout or WAL. | Step 6 |

## Checklist scorecard
| Area | Assessment |
|---|---|
| Design | Adequate. Core code depends on small interfaces. O7 and O8 are the weak spots. |
| Functionality | Adequate for its slice. F1 to F7 were real defects. O1 and O2 matter most. |
| Complexity | Acceptable. `assemble()` is long and does five jobs, which is the next thing to split. |
| Tests | Good for behaviour that is claimed. 49 tests. None cover concurrency, crashes or large inputs. |
| Naming | Good. Blocker and task names say what they mean. |
| Comments | Few and aimed at why (for example, the discovery assumptions). |
| Style | Not verified. The line-length and unused-import checks I ran are not a substitute for ruff. |
| Documentation | Now matches the code. START-HERE, REVIEW, VALIDATION and LLD were updated together. |

## SOLID check
- Single responsibility: modules are focused. `assemble()` and `cli.main()` are not.
- Open/closed: a new storage backend can be added without changing the service. Only one backend exists, so this is not yet demonstrated.
- Liskov: the two catalogs behaved differently (F3). Fixed and tested.
- Interface segregation: the ports are small. O8 is the gap.
- Dependency inversion: the service depends on ports. The CLI builds the concrete classes, which is the right place for that.

## Reading order
`domain.py` then `ports.py`, `assembly.py`, `tasks.py`, `service.py`, `storage.py`, `cli.py`.
