# Interview preparation

Personal notes for explaining this work. Answer from what is actually built. If you are asked about something below the line "Not built", say so plainly: the brief rewards a clear boundary (brief p.8).

## 60-second summary
The brief says the decisions are mostly not hard and that assembling enough evidence to be allowed to make them is the whole cost (p.3). So I built the evidence step. For each alert the tool finds product, study and SOP candidates, says why each is or is not usable, lists what a person must resolve, and saves the package so it can be replayed. It never makes a product decision. Every case ends BLOCKED because the source documents, approvals and batch history are not available to it.

## Questions to expect, with honest answers
**What did you decide the problem was?** Evidence assembly and preservation, not label prediction. Evidence: p.3 ("whole cost"), March inspection (p.3), AUD-2603 in workbook tab 14.

**Why does everything end BLOCKED? Is that useful?** BLOCKED is the honest result when authority is missing. The usefulness is in the tasks: each says what is missing, which role resolves it, what evidence counts. 420 of 420 blocked is not an accuracy result.

**Walk me through EXC-107133.** Alert row 221. Product candidate: master row 57. Studies: 105 (pen, excursion, no rejection reason but still unverified), 106 (unreadable), 107 (vial), 108 (cited by the master, but vial, accelerated, partly readable, no allowance). SOPs: rows 203 and 204 overlap. The master says cumulative 72 h above 8 C; the pen study says one excursion up to 6 h below 15 C. I do not pick a winner or combine them; a task asks QA how they relate.

**Why not reproduce RELEASE_WITH_NOTE?** The index rows cannot justify it. The brief says the answer was right but the right to sign it took the other hundred minutes (p.3).

**What does replay prove?** That the same stored inputs give the same package, and that stored data was not edited. It does not prove the inputs are true.

**What is your tenant isolation story?** Built: tenant check on every entry point, tenant-keyed storage, replay refused for another tenant, captured snapshot holds only same-tenant rows. Not built: authentication. The tenant is a local argument, so this is scoping, not security.

**Notification versus disposition?** Two clocks (p.2). The obligation is saved before assembly, survives an assembly failure, and survives a restart (all tested). The deadline is the imported historical window, not a qualified legal calendar. An imported "N" is not a qualified "not required".

**What breaks first at 3am?** Honest answer: nothing monitors it. There is no alerting, no authenticated API and no real notification delivery. The design in HLD.md lists the metrics I would add first: oldest deadline, unresolved tasks by role, replay divergence, archive failures.

**A new firmware bulletin arrives. How does this absorb it?** The bulletin is a blocker today (firmware TT-2.14.3) and a task asks QA to assess applicability and sensitivity. The 1.8 C figure is treated as uncertainty, not a fixed correction. Reassessment as a linked new package is designed, not built.

**Cost?** The tool makes no model calls. That does not make operation free: ingestion, indexing, storage and seven-year retention are a separate line in workbook tab 13 and still need sizing.

## The two things you are least comfortable with (they will pick these)
1. No authentication or signing. Say what the design is (HLD.md, LLD.md) and that it is not built.
2. The discovery step is lexical. It can include a wrong study or miss a right one, which is why nothing it finds carries authority. Also, the allowance-wording task over-flags: 170 of 420 events.

## Not built
Authenticated API, qualified or dual signing, source-document verification, approved identity mapping, batch or once-only ledger, calendars and delivery, immutable archive, task closure, measured scale, Postgres.

## Do not claim
"Production ready", "validated", "secure", "scales", "accurate". The checks that exist are listed in VALIDATION.md.

## 90-second demo
1. `python -m sentinel_review.demo demo.xlsx`
2. `sentinel-review --db demo.sqlite review demo.xlsx --event DEMO-1 --tenant T-DEMO-A --out demo-out.json`
3. Open `demo-out.json`: show `status` BLOCKED, `final_disposition` null, the blockers and `resolution_tasks`.
4. `sentinel-review --db demo.sqlite replay BUNDLE_ID --tenant T-DEMO-A` (identical: true).
5. Repeat step 4 with `--tenant T-DEMO-B` and show it is refused.

## Still to do before you submit
Add the real hours you spent, keep the original chat sessions, and fill the covering note (brief p.8).
