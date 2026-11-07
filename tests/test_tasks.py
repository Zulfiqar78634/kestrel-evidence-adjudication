import unittest
from sentinel_review.assembly import assemble
from sentinel_review.domain import SourceRow
from sentinel_review.service import ReviewService, replay
from sentinel_review.storage import SQLiteRepository
from sentinel_review.tasks import TASK_TEMPLATES
from test_review import MemoryCatalog, event

KNOWN_BLOCKERS = [
    "SOURCE_CONTENT_NOT_VERIFIED", "SITE_ACCEPTANCE_NOT_ESTABLISHED", "BATCH_HISTORY_NOT_ESTABLISHED",
    "PRODUCT_MAPPING_REQUIRES_APPROVAL", "PRODUCT_CANDIDATE_MISSING_OR_AMBIGUOUS", "SOP_REVISION_OVERLAP",
    "NO_DATED_SOP_CANDIDATE", "EVENT_TIME_INVALID", "EVENT_TIME_CONFLICT", "MEASUREMENTS_INVALID_OR_MISSING",
    "BULLETIN_APPLICABILITY_AND_SENSITIVITY_REQUIRE_REVIEW",
]
FIELDS = {"id", "reason", "role", "evidence_requested", "completion_criterion", "sources", "status", "detail"}


def tasks_for(reason, result):
    return [t for t in result["resolution_tasks"] if t["reason"] == reason]


class TaskTests(unittest.TestCase):
    def setUp(self):
        self.catalog = MemoryCatalog()

    def result(self, **changes):
        return assemble(self.catalog, event(**changes), "A")

    def test_every_blocker_has_a_task(self):
        result = self.result()
        reasons = {t["reason"] for t in result["resolution_tasks"]}
        for blocker in result["blockers"]:
            self.assertIn(blocker, reasons)

    def test_templates_cover_every_known_blocker(self):
        for blocker in KNOWN_BLOCKERS:
            self.assertIn(blocker, TASK_TEMPLATES)

    def test_task_shape_and_no_named_assignee(self):
        for task in self.result()["resolution_tasks"]:
            self.assertEqual(set(task), FIELDS)
            self.assertEqual(task["status"], "OPEN")
            for key in ("role", "evidence_requested", "completion_criterion"):
                self.assertTrue(task[key].strip())
            self.assertTrue(task["sources"])

    def test_ids_unique_and_deterministic(self):
        first, second = self.result(), self.result()
        self.assertEqual(first["resolution_tasks"], second["resolution_tasks"])
        ids = [t["id"] for t in first["resolution_tasks"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_open_tasks_never_unblock(self):
        result = self.result()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIsNone(result["final_disposition"])

    def test_overlap_task_cites_both_revisions(self):
        self.catalog.tables["05_SOP_Index"].append(
            SourceRow("05_SOP_Index", 3, dict(self.catalog.tables["05_SOP_Index"][0].values)))
        rows = {s["row"] for t in tasks_for("SOP_REVISION_OVERLAP", self.result()) for s in t["sources"]
                if s["sheet"] == "05_SOP_Index"}
        self.assertEqual(rows, {2, 3})

    def test_rejected_study_gets_confirmation_task(self):
        self.catalog.tables["06_Stability_Index"][0].values["product_text_as_written"] = "Demo vial"
        found = tasks_for("STUDY_REJECTION_CONFIRMATION", self.result())
        self.assertEqual(len(found), 1)
        self.assertIn("PRESENTATION_CONFLICT", found[0]["detail"])
        self.assertEqual(found[0]["sources"][-1], {"sheet": "06_Stability_Index", "row": 2})

    def test_clean_study_gets_verification_task_not_approval(self):
        found = tasks_for("STUDY_APPLICABILITY_VERIFICATION", self.result())
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["status"], "OPEN")

    def test_allowance_wording_conflict_task(self):
        self.catalog.tables["02_Product_Master"][0].values["permitted_excursion_text"] = "Cumulative 10 h above 8 C"
        found = tasks_for("ALLOWANCE_WORDING_RELATIONSHIP", self.result())
        self.assertEqual(len(found), 1)
        self.assertIn("No combined rule", found[0]["completion_criterion"])

    def test_no_allowance_task_when_wording_matches(self):
        self.catalog.tables["02_Product_Master"][0].values["permitted_excursion_text"] = "Synthetic text only"
        self.assertEqual(tasks_for("ALLOWANCE_WORDING_RELATIONSHIP", self.result()), [])

    def test_missing_measurement_task(self):
        self.assertTrue(tasks_for("MEASUREMENTS_INVALID_OR_MISSING", self.result(min_temp_c=None)))

    def test_tasks_survive_replay(self):
        repo = SQLiteRepository(":memory:")
        self.addCleanup(repo.close)
        saved = ReviewService(self.catalog, repo).review(event(), "A")
        self.catalog.tables.clear()
        replayed = replay(repo, "A", saved["bundle_id"])
        self.assertTrue(replayed["identical"])
        self.assertEqual(replayed["result"]["resolution_tasks"], saved["result"]["resolution_tasks"])


if __name__ == "__main__":
    unittest.main()
