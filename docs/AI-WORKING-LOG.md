# D. Working log

A factual record of how this was produced, not a polished narrative.

1. Request: a complete interview-ready submission built from the original brief and workbook. First delivery was a small synthetic single-file kernel (`kestrel.py`) with unit tests. The user correctly pointed out it did not cover HLD, LLD, system design or original-data work. That kernel remains in the repo for history.
2. The brief and the workbook (all 15 sheets) were then read directly. EXC-107133 rows were inspected: event row 221, product row 57, studies rows 105-108, SOP rows 203-204.
3. Kept: treat the problem as evidence assembly; keep unresolved authority explicit; separate notification from disposition. Rejected: reproducing the historical RELEASE_WITH_NOTE, using historical triage or master text as proof, calling hash replay complete audit evidence, treating a matching row as approved authority.
4. Built `sentinel_review/` as a small modular slice, ran it on all 420 events, replayed all 420, and ran the tests, including one against the private workbook.
5. Another assistant's repository was reviewed separately; no code from it is in this repository.
6. Mistakes caught along the way: counting tests from different code versions together; describing a design as if it were built; claiming a commit that had not been pushed. Each was corrected when the user challenged it.
7. Not done: no remote CI result is claimed here, no deployment, no Claude Code skills were installed, no clinical review took place.
8. The author should add the real hours spent and keep the original chat sessions, as the brief requests.
