# Start here

Plain-language guide. It follows the Diataxis idea of four kinds of page: explanation (why), tutorial (try it), how-to (do a task) and reference (look things up).

## 1. Explanation: what is this?
A medicine box travels in a refrigerator. A thermometer beeps when it gets too warm or cold. The beep means "please check". It does not mean "throw it away" and it does not mean "ignore it".

To decide, a qualified person needs the right facts: which medicine it is, which study says how much warmth it can take, which company rule applies on that date and at that site, and what happened to the same batch before. Those facts sit in many systems under different names. Gathering them is most of the work.

This tool does the gathering step. For each beep it finds candidate records, says why each one is or is not usable, and lists what a person still has to confirm. It never decides what happens to the medicine. Every result says `BLOCKED`, because the tool does not have the original documents or any approvals.

## 2. Tutorial: try it in five minutes (no private data)
```sh
git clone https://github.com/Zulfiqar78634/kestrel-evidence-adjudication
cd kestrel-evidence-adjudication
python -m pip install -e ".[dev]"
python -m sentinel_review.demo demo.xlsx
sentinel-review --db demo.sqlite review demo.xlsx --event DEMO-1 --tenant T-DEMO-A --out demo-out.json
```
Open `demo-out.json`. You will see `"status": "BLOCKED"`, a list of blockers, and `resolution_tasks`. Each task says what is missing, which role should resolve it and what evidence would count. Copy the `bundle_id` and run:
```sh
sentinel-review --db demo.sqlite replay BUNDLE_ID --tenant T-DEMO-A
sentinel-review --db demo.sqlite replay BUNDLE_ID --tenant T-DEMO-B
```
The first prints `"identical": true`. The second is refused with exit code 2, because that bundle belongs to another tenant.

## 3. How-to guides
- Run all tests: `python -m unittest discover -s tests -v`
- Check lint and types: `ruff check sentinel_review` and `mypy`
- Review every tenant in a workbook (operator only): add `--all-tenants` instead of `--tenant`
- See pending notification obligations: `sentinel-review --db demo.sqlite obligations --tenant T-DEMO-B`
- Use the real workbook: keep it outside the repo and pass its path. Never commit it or the generated JSON and SQLite files.

## 4. Reference
| Word | Meaning |
|---|---|
| Tenant | One customer company. Its data is kept apart from the others. |
| Candidate | A record the tool found. Not approved. |
| Blocker | A named reason the case cannot be decided yet. |
| Resolution task | What a person must bring to clear a blocker. Always OPEN. |
| Obligation | A regulator-notification deadline imported from the data. Separate from the product decision. |
| Bundle | The saved result plus the rows it used, identified by a hash. |
| Replay | Re-run on the saved rows and check the result is identical. |

| Exit code | Meaning |
|---|---|
| 0 | Success |
| 2 | Refused or failed. A JSON error is printed to stderr. |

More: `docs/REVIEW.md` (what is weak), `docs/VALIDATION.md` (what was run), `docs/INTERVIEW.md` (talking points), `docs/HLD.md` and `docs/LLD.md` (design).
