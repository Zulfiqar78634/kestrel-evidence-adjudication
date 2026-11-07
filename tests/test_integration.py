import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from kestrel import Archive, demo, digest, evaluate

ROOT = Path(__file__).resolve().parents[1]


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = str(Path(self.temp.name) / "evidence.sqlite")

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "kestrel.py"), "--db", self.db, *args], capture_output=True, text=True, timeout=15)

    def test_cli_demo_and_restart_replay(self):
        run = self.cli("demo")
        self.assertEqual(run.returncode, 0, run.stderr)
        first = json.loads(run.stdout)
        replay = self.cli("replay", first["snapshot_id"], "--tenant", "demo")
        self.assertEqual(replay.returncode, 0, replay.stderr)
        self.assertTrue(json.loads(replay.stdout)["identical"])

    def test_cli_wrong_tenant_denied(self):
        first = json.loads(self.cli("demo").stdout)
        denied = self.cli("replay", first["snapshot_id"], "--tenant", "other")
        self.assertNotEqual(denied.returncode, 0)
        self.assertEqual(denied.stdout, "")

    def test_cli_missing_measurements(self):
        case = demo()
        case["measurements"] = {}
        path = Path(self.temp.name) / "case.json"
        path.write_text(json.dumps(case))
        run = self.cli("evaluate", str(path), "--tenant", "demo")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["result"]["status"], "EVIDENCE_INCOMPLETE")

    def test_invalid_json_fails_without_success_output(self):
        path = Path(self.temp.name) / "bad.json"
        path.write_text("{broken")
        run = self.cli("evaluate", str(path), "--tenant", "demo")
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(run.stdout, "")

    def test_snapshot_survives_restart(self):
        archive = Archive(self.db)
        try:
            key, _ = archive.save(demo(), "demo")
        finally:
            archive.close()
        reopened = Archive(self.db)
        try:
            self.assertTrue(reopened.replay(key, "demo")["identical"])
        finally:
            reopened.close()

    def test_future_evidence_blocked(self):
        case = demo()
        case["evidence"][0]["valid_from"] = "2027-01-01T00:00:00Z"
        self.assertEqual(evaluate(case, "demo")["status"], "EVIDENCE_INCOMPLETE")

    def test_invalid_order_blocked(self):
        case = demo()
        case["alert_received"] = "2026-01-01T00:00:00Z"
        self.assertIn("INVALID_EVENT_ORDER", evaluate(case, "demo")["issues"])

    def test_unapproved_evidence_blocked(self):
        case = demo()
        case["evidence"][0]["approved"] = False
        self.assertEqual(evaluate(case, "demo")["status"], "EVIDENCE_INCOMPLETE")

    def test_does_not_mutate_inputs(self):
        case = demo()
        before = digest(case)
        evaluate(case, "demo")
        self.assertEqual(digest(case), before)

    def test_reversed_extrema_blocked(self):
        case = demo()
        case["measurements"] = {"min_c": 9, "max_c": 3}
        self.assertEqual(evaluate(case, "demo")["temperature_state"], "UNKNOWN")
