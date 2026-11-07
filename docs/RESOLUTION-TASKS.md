# Resolution tasks

A blocker says something is missing. A resolution task says what, who must resolve it and what would count as resolved. Code: `sentinel_review/tasks.py`. The tasks sit in `resolution_tasks` in each result, next to the blockers described in `LLD.md`.

## Fields
| Field | Meaning |
|---|---|
| `id` | `EVENT:REASON` plus `:STUDY@ROW` for study tasks. Unique and stable across runs. |
| `reason` | The blocker code, or a study-level code (below). |
| `role` | A role label such as "Site QA". Never a named person. |
| `evidence_requested` | What a person must bring. |
| `completion_criterion` | What "resolved" means. |
| `sources` | Workbook sheet and row that the task refers to, sorted. The alert row is always included. |
| `status` | Always `OPEN`. |
| `detail` | Rejection reasons, or the two allowance wordings being compared. |

## Task kinds
One task per blocker, using the templates in `TASK_TEMPLATES`. Three more are created per study candidate:
- `STUDY_APPLICABILITY_VERIFICATION` for a study with no rejection reason. It asks for the original report. It is not an approval.
- `STUDY_REJECTION_CONFIRMATION` for a study with rejection reasons. It asks someone to confirm or overturn them.
- `ALLOWANCE_WORDING_RELATIONSHIP` when a study without rejection reasons has permitted-excursion wording that differs from the product master's. It asks QA how the two relate. The tool does not combine them.

## EXC-107133 (real workbook, 10 tasks)
Six blocker tasks, one verification task for STB-2738 (06 row 105), three rejection tasks for STB-4400, STB-3312 and STB-3584 (rows 106, 107, 108), and one allowance-wording task comparing the master's "Cumulative 72 h above 8 C permitted across shelf life" (02 row 57) with STB-2738's "One excursion, up to 6 h below 15 C". No source is chosen as the winner.

## Rules the code enforces
- Every blocker has a task, and every task has at least one source. A test checks both.
- Tasks are deterministic: the same inputs give the same task list.
- There is no function that closes a task or removes a blocker. That is deliberate: closing needs an authenticated approver and approved evidence, which are Step 5.
- Tasks are saved inside the bundle and come back identical on replay.

## Limits
- Role names and template wording are this project's, not Kestrel's organisation.
- The allowance-wording task fires on any text difference, so it will over-flag. On the 420-event sample, 170 events have one. That is a count of text differences, not of real conflicts.
- Tasks do not rank urgency and are not linked to the notification deadline yet.
