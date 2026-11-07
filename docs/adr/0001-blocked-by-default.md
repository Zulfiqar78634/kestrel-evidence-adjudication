# ADR 0001: Results are BLOCKED by default and never closed from history

## Status
Accepted.

## Context
The brief says the decisions are mostly not hard and that assembling enough evidence to be allowed to make them is the whole cost (p.3). A past attempt let a model draft decisions and it cited studies that did not exist (p.5). The workbook warns that past auto-closures were never audited and that its recommendation column holds assistant drafts (00_README). This tool has the alert rows and index rows, but not the source documents, approvals or batch history.

## Decision
Every result is `BLOCKED` with `final_disposition` null. Each blocker produces an OPEN resolution task. Historical triage and final-disposition fields are stored but never used as evidence. No code path closes a task or removes a blocker.

## Consequences
Easier: nothing can be mistaken for an approval; replay and review are simple; the output says exactly what a person must resolve.
Harder: the tool cannot yet reduce reviewer work by closing noise alerts; that needs approved evidence and authenticated approvers (roadmap Step 5). Every one of the 420 sample events ends BLOCKED, which is a statement about missing authority and not an accuracy result.
