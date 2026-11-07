# A. Position

## What the problem is
Kestrel sells inspection-ready custody evidence. The brief's key observation is that assembling enough evidence to be allowed to decide is the whole cost (brief p.3, section 2), and that the outcome string alone could not be defended later (p.3; AUD-2603 in workbook 14). This is an evidence-assembly and preservation problem, not a label-prediction problem.

## What to build, in order
1. Evidence applicability: tenant-scoped identity, study and SOP candidates with explicit rejection reasons and unresolved authority.
2. Preserved basis: captured inputs, integrity check and replay.
3. Independent notification obligations, admitted before and regardless of evidence assembly (brief p.2; INC-2502).
4. QA-qualified closure policies for verified noise, only after sources and mappings are approved.
5. Reviewer workflow with authenticated, evidence-bound sign-off. Automation of closures is acceptable; automation of regulated decisions is not (brief p.6, Dr Rao).

## What is deliberately left alone
Live integration with the nine systems, OCR of annexures, replacing the 2,400 rules, any LLM on the decision path, claims and invoicing, and a full reviewer UI. They need source contracts and qualification the pack does not supply. The brief rewards drawing the boundary explicitly (brief p.8).

## Running slice and what it shows for EXC-107133
Source rows: event 01 row 221, product 02 row 57, studies 06 rows 105-108, SOPs 05 rows 203-204. The tool surfaces STB-2738 (pen excursion study) as a candidate without approving it; flags the master-cited STB-3584 as a vial, accelerated, partly readable study with no indexed allowance; and exposes the SOP revision overlap. Result: BLOCKED with named unresolved questions. The historical RELEASE_WITH_NOTE is not reproduced because the supplied index rows cannot justify it by themselves.

## Positions taken where the pack is silent or conflicting
- The pack never says how a single-excursion allowance interacts with a cumulative allowance. STB-2738 says one excursion up to 6 h below 15 C; the master says cumulative 72 h above 8 C. Both are kept; QA must say which governs.
- Date-only SOP end dates are treated as inclusive for discovery only.
- Historical reportability flags are imported references, not qualified applicability; blank becomes UNKNOWN.
- The 420 events are stratified, so no rate computed from them is a production rate (workbook 00_README).

## Board outcomes
Under-24h median disposition, 70% human-free closure, 7-year basis retrieval within an hour, no late notifications and the rollout dates are targets (brief p.6). This slice demonstrates none of them. Keep notification latency, signed-disposition latency and machine latency as separate measures.

## Cost
Workbook 13 gives USD 0.06 per screened alert and USD 1.10 per case reaching a reviewer for inference and retrieval, against 11,400 alerts and 2,050 cases a month; the brief separately quotes USD 3,000 a month for model spend. The two framings are not reconciled in the pack and need a factual answer. Ingestion, indexing, storage and seven-year retention are a separate line and still need sizing. This slice makes no model calls, which does not make operation free.

## Questions for Kestrel
Who approves disputed aliases and site mappings? Which site governs when origin and destination SOPs differ? How is exposure history certified complete? Which source versions existed when a past decision was signed? Which programme calendars apply for next-business-day filings?
