import copy
import unittest
from kestrel import Archive, demo, evaluate, parse_limits, temperature_state


class KernelTests(unittest.TestCase):
    def setUp(self):
        self.case = demo()

    def result(self):
        return evaluate(self.case, "demo")

    def test_complete_is_candidate_not_disposition(self):
        self.assertEqual(self.result()["status"], "CLOSURE_CANDIDATE")
        self.assertTrue(self.result()["human_disposition_required"])

    def test_missing_readings(self):
        self.case["measurements"] = {}
        self.assertEqual(self.result()["status"], "EVIDENCE_INCOMPLETE")

    def test_mean_cannot_replace_extrema(self):
        self.case["measurements"] = {"mean_c": 5}
        self.assertEqual(self.result()["temperature_state"], "UNKNOWN")

    def test_historical_triage_cannot_override(self):
        self.case["measurements"] = {}
        self.case["triage_outcome"] = "duplicate; no product loaded"
        self.assertEqual(self.result()["status"], "EVIDENCE_INCOMPLETE")

    def test_upper_only(self):
        self.assertEqual(temperature_state({"max_c": 24}, parse_limits("below 25 C")), "WITHIN")

    def test_upper_only_strict_equality(self):
        self.assertEqual(temperature_state({"max_c": 25}, parse_limits("below 25 C")), "OUTSIDE")

    def test_inclusive_negative_limit(self):
        self.assertEqual(temperature_state({"max_c": -150}, parse_limits("≤ −150 °C")), "WITHIN")

    def test_lower_only(self):
        self.assertEqual(temperature_state({"min_c": 3}, parse_limits("above 2 C")), "WITHIN")

    def test_negative_range(self):
        self.assertEqual(temperature_state({"min_c": -79, "max_c": -61}, parse_limits("-80 to -60 C")), "WITHIN")

    def test_ambiguous_text(self):
        with self.assertRaises(ValueError):
            parse_limits("controlled room temperature")

    def test_nonfinite(self):
        self.case["measurements"]["max_c"] = "NaN"
        self.assertEqual(self.result()["temperature_state"], "UNKNOWN")

    def test_uncertainty_preserves_observation(self):
        self.case["under_reading_bound_c"] = "1.8"
        self.assertEqual(self.result()["temperature_state"], "UNCERTAIN")
        self.assertEqual(self.case["measurements"]["max_c"], 7)

    def test_excursion_is_qa_not_destroy(self):
        self.case["measurements"]["max_c"] = 12
        self.assertEqual(self.result()["status"], "READY_FOR_QA")

    def test_wrong_caller_tenant(self):
        with self.assertRaises(PermissionError):
            evaluate(self.case, "other")

    def test_wrong_evidence_tenant(self):
        self.case["evidence"][0]["tenant_id"] = "other"
        self.assertEqual(self.result()["status"], "EVIDENCE_INCOMPLETE")

    def test_wrong_presentation(self):
        self.case["evidence"][-1]["presentation"] = "vial"
        self.assertIn("STABILITY_AUTHORITY_UNRESOLVED", self.result()["issues"])

    def test_ambiguous_sop(self):
        self.case["evidence"].append(copy.deepcopy(self.case["evidence"][3]))
        self.assertIn("SOP_MISSING_OR_AMBIGUOUS", self.result()["issues"])

    def test_effective_end_exclusive(self):
        self.case["evidence"][3]["valid_to"] = self.case["excursion_start"]
        self.assertIn("SOP_AUTHORITY_UNRESOLVED", self.result()["issues"])

    def test_naive_timestamp(self):
        self.case["excursion_start"] = "2026-01-02T10:00:00"
        self.assertIn("INVALID_EVENT_TIME", self.result()["issues"])

    def test_once_only_history_not_assumed(self):
        self.case["once_only"] = True
        self.assertIn("EXPOSURE_HISTORY_AND_POLICY_REQUIRE_QA", self.result()["issues"])

    def test_additional_constraints_block(self):
        self.case["additional_constraints"] = ["do not freeze"]
        self.assertEqual(self.result()["status"], "EVIDENCE_INCOMPLETE")

    def test_determinism(self):
        self.assertEqual(self.result(), self.result())

    def test_archive_scoping_idempotency_replay_tampering(self):
        archive = Archive(":memory:")
        try:
            key, _ = archive.save(self.case, "demo")
            self.assertEqual(key, archive.save(self.case, "demo")[0])
            self.assertTrue(archive.replay(key, "demo")["identical"])
            with self.assertRaises(LookupError):
                archive.replay(key, "other")
            archive.db.execute("UPDATE snapshots SET payload=replace(payload, 'DEMO-001', 'EVIL-001')")
            with self.assertRaises(ValueError):
                archive.replay(key, "demo")
        finally:
            archive.close()
