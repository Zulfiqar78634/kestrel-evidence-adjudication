# Resolution tasks

A blocker says something is missing. A resolution task says what, who must resolve it and what would count as resolved. Code: `sentinel_review/tasks.py`. Tasks sit in `resolution_tasks` in each result, next to the blockers described in `LLD.md`.

## Fields
| Field | Meaning |
|---|---|
| `id` | `EVENT:REASON`, plus `:STUDY@ROW` for study tasks. Unique and stable across runs. |
| `reason` | The blocker code, or a study-level code (below). |
| `role` | A role label such as "Site QA". Never a named person. |
| `evidence_requested` | What a person must bring. |
| `completion_criterion` | What "resolved" means. |
| `sources` | Workbook sheet and row the task refers to, sorted. The alert row is always included. |
| `status` | Always `OPEN`. |
| `detail` | Rejection reasons, or the two allowance wordings being compared. |

## Task kinds
One task per blocker, from `TASK_TEMPLATES`. Per study candidate there is one more:
- `STUDY_APPLICABILITY_VERIFICATION` when the study has no rejection reason. It asks for the original report. It is not an approval.
- `STUDY_REJECTION_CONFIRMATION` when it has rejection reasons. It asks someone to confirm or overturn them.
- `ALLOWANCE_WORDING_RELATIONSHIP` as well, when a study without rejection reasons words the permitted excursion differently from the product master. It asks QA how the two relate. The tool does not combine them.

## EXC-107133 (real workbook, 10 tasks)
Six blocker tasks; one verification task for STB-2738 (06 row 105); three rejection tasks for STB-4400, STB-3312 and STB-3584 (rows 106, 107, 108); and one allowance-wording task comparing the master's "Cumulative 72 h above 8 C permitted across shelf life" (02 row 57) with STB-2738's "One excursion, up to 6 h below 15 C". No source is chosen as the winner.

## Rules the code enforces
- Every blocker has a task and every task has at least one source. Tests check both.
- The same inputs give the same task list.
- Nothing closes a task or removes a blocker. That is deliberate: closing needs an authenticated approver and approved evidence (roadmap Step 5).
- Tasks are saved in the bundle and come back identical on replay.

## Limits
- Role names and template wording are this project's, not Kestrel's organisation.
- On the 420-event sample, 170 events have an allowance-wording task. I checked all 170: none differ only by punctuation or spacing, so they are real wording differences. A wording difference is still not a proven conflict; the study may simply be phrased differently.
- Tasks do not rank urgency and are not linked to the notification deadline.
