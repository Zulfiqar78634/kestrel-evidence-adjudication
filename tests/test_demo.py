import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from sentinel_review.demo import build_demo_workbook
from sentinel_review.workbook import WorkbookCatalog

ROOT = Path(__file__).resolve().parents[1]


class DemoWorkbookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workbook = Path(self.temp.name) / "demo.xlsx"
        self.db = str(Path(self.temp.name) / "demo.sqlite")
        build_demo_workbook(self.workbook)

    def cli(self, *args):
        return subprocess.run([sys.executable, "-m", "sentinel_review.cli", "--db", self.db, *args],
                              cwd=ROOT, capture_output=True, text=True, timeout=60)

    def test_demo_data_is_clearly_synthetic(self):
        catalog = WorkbookCatalog(self.workbook)
        tenants = {r.values["tenant_code"] for r in catalog.rows("01_Excursion_Events")}
        self.assertTrue(all(t.startswith("T-DEMO") for t in tenants))
        self.assertIn("SYNTHETIC", str(catalog.rows("00_README")[0].values))

    def test_cli_review_replay_and_tasks(self):
        out = Path(self.temp.name) / "out.json"
        run = self.cli("review", str(self.workbook), "--event", "DEMO-1", "--tenant", "T-DEMO-A", "--out", str(out))
        self.assertEqual(run.returncode, 0, run.stderr)
        saved = json.loads(out.read_text())[0]
        reasons = {t["reason"] for t in saved["result"]["resolution_tasks"]}
        self.assertTrue({"SOP_REVISION_OVERLAP", "STUDY_REJECTION_CONFIRMATION",
                         "STUDY_APPLICABILITY_VERIFICATION", "ALLOWANCE_WORDING_RELATIONSHIP"} <= reasons)
        replay = self.cli("replay", saved["bundle_id"], "--tenant", "T-DEMO-A")
        self.assertEqual(replay.returncode, 0, replay.stderr)
        self.assertTrue(json.loads(replay.stdout)["identical"])

    def test_cli_wrong_tenant_cannot_replay(self):
        out = Path(self.temp.name) / "out.json"
        self.cli("review", str(self.workbook), "--event", "DEMO-1", "--tenant", "T-DEMO-A", "--out", str(out))
        bundle = json.loads(out.read_text())[0]["bundle_id"]
        denied = self.cli("replay", bundle, "--tenant", "T-DEMO-B")
        self.assertNotEqual(denied.returncode, 0)
        self.assertEqual(denied.stdout, "")

    def test_reportable_demo_event_creates_obligation(self):
        out = Path(self.temp.name) / "out.json"
        self.assertEqual(self.cli("review", str(self.workbook), "--tenant", "T-DEMO-B", "--out", str(out)).returncode, 0)
        queue = json.loads(self.cli("obligations", "--tenant", "T-DEMO-B").stdout)
        self.assertEqual(queue[0]["state"], "PENDING_REVIEW")

    def test_missing_measurement_demo_event_is_blocked(self):
        out = Path(self.temp.name) / "out.json"
        self.cli("review", str(self.workbook), "--event", "DEMO-2", "--tenant", "T-DEMO-A", "--out", str(out))
        blockers = json.loads(out.read_text())[0]["result"]["blockers"]
        self.assertIn("MEASUREMENTS_INVALID_OR_MISSING", blockers)

    def test_module_entry_point_writes_workbook(self):
        target = Path(self.temp.name) / "made.xlsx"
        run = subprocess.run([sys.executable, "-m", "sentinel_review.demo", str(target)],
                             cwd=ROOT, capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(target.exists() and target.stat().st_size > 0)


if __name__ == "__main__":
    unittest.main()
