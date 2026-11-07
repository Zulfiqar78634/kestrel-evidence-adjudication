import os
import tempfile
import unittest
from pathlib import Path
from sentinel_review.assembly import assemble
from sentinel_review.domain import SourceRow, gtin
from sentinel_review.service import ReviewService, replay
from sentinel_review.storage import SQLiteRepository
from sentinel_review.workbook import WorkbookCatalog


class MemoryCatalog:
    def __init__(self):
        self.tables = {
            "02_Product_Master": [SourceRow("02_Product_Master", 2, {"tenant_code": "A", "gtin": "00000000000001", "brand_as_labelled": "Demo pen", "stability_study_ref": "S1"})],
            "05_SOP_Index": [SourceRow("05_SOP_Index", 2, {"tenant_code": "A", "doc_id": "D1", "title": "Excursion management", "effective_from": "2025-01-01", "effective_to": None})],
            "06_Stability_Index": [SourceRow("06_Stability_Index", 2, {"tenant_code": "A", "study_ref": "S1", "product_text_as_written": "Demo pen", "study_type": "Excursion", "readable": "Y", "permitted_excursion_text": "Synthetic text only"})]}

    def rows(self, name):
        return tuple(self.tables[name])


def event(**changes):
    values = {"tenant_code": "A", "event_id": "TEST-1", "product_ref_as_received": "00000000000001", "excursion_start_utc": "2026-01-02 10:00", "alert_ts_utc": "2026-01-02 10:01", "min_temp_c": 3, "max_temp_c": 7, "regulator_reportable": "Y", "reg_window_hours": 72}
    values.update(changes)
    return SourceRow("01_Excursion_Events", 2, values)


class UnitTests(unittest.TestCase):
    def setUp(self):
        self.catalog = MemoryCatalog()
        self.repo = SQLiteRepository(":memory:")
        self.addCleanup(self.repo.close)

    def test_gtin_formats(self):
        self.assertEqual(gtin("8.901234500035e+12"), "08901234500035")
        self.assertEqual(gtin("08901234500035"), "08901234500035")

    def test_tenant_denied(self):
        with self.assertRaises(PermissionError):
            assemble(self.catalog, event(), "B")

    def test_no_product_disposition(self):
        result = assemble(self.catalog, event(), "A")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIsNone(result["final_disposition"])

    def test_missing_temperature(self):
        self.assertEqual(assemble(self.catalog, event(min_temp_c=None), "A")["measurement"], "UNKNOWN")

    def test_nan_temperature(self):
        self.assertEqual(assemble(self.catalog, event(max_temp_c="NaN"), "A")["measurement"], "UNKNOWN")

    def test_reversed_temperature(self):
        self.assertEqual(assemble(self.catalog, event(min_temp_c=9, max_temp_c=3), "A")["measurement"], "UNKNOWN")

    def test_historical_labels_do_not_drive_result(self):
        first = assemble(self.catalog, event(), "A")
        second = assemble(self.catalog, event(triage_outcome="duplicate, no product loaded", final_disposition="DESTROY"), "A")
        self.assertEqual(first, second)

    def test_duplicate_product_ambiguous(self):
        self.catalog.tables["02_Product_Master"] *= 2
        self.assertIn("PRODUCT_CANDIDATE_MISSING_OR_AMBIGUOUS", assemble(self.catalog, event(), "A")["blockers"])

    def test_future_sop_not_candidate(self):
        self.catalog.tables["05_SOP_Index"][0].values["effective_from"] = "2027-01-01"
        self.assertEqual(assemble(self.catalog, event(), "A")["sop_candidates"], [])

    def test_overlapping_sop_exposed(self):
        self.catalog.tables["05_SOP_Index"].append(SourceRow("05_SOP_Index", 3, dict(self.catalog.tables["05_SOP_Index"][0].values)))
        self.assertIn("SOP_REVISION_OVERLAP", assemble(self.catalog, event(), "A")["blockers"])

    def test_wrong_presentation_rejected_for_discovery(self):
        self.catalog.tables["06_Stability_Index"][0].values["product_text_as_written"] = "Demo vial"
        self.assertIn("PRESENTATION_CONFLICT", assemble(self.catalog, event(), "A")["study_candidates"][0]["discovery_rejections"])

    def test_obligation_survives_assembly_failure(self):
        self.catalog.tables.pop("06_Stability_Index")
        with self.assertRaises(KeyError):
            ReviewService(self.catalog, self.repo).review(event(), "A")
        self.assertEqual(len(self.repo.obligations("A")), 1)

    def test_obligation_idempotent(self):
        service = ReviewService(self.catalog, self.repo)
        service.review(event(), "A")
        service.review(event(), "A")
        self.assertEqual(len(self.repo.obligations("A")), 1)
        self.assertEqual(self.repo.obligations("A")[0]["state"], "PENDING_REVIEW")

    def test_unknown_reportability_never_false(self):
        self.repo.register_obligation(event(regulator_reportable=None), "A")
        self.assertEqual(self.repo.obligations("A")[0]["reportability"], "UNKNOWN")

    def test_replay_uses_snapshot(self):
        result = ReviewService(self.catalog, self.repo).review(event(), "A")
        self.catalog.tables.clear()
        self.assertTrue(replay(self.repo, "A", result["bundle_id"])["identical"])

    def test_tampering_denied(self):
        result = ReviewService(self.catalog, self.repo).review(event(), "A")
        self.repo.db.execute("UPDATE bundles SET payload=replace(payload, 'TEST-1', 'EVIL-1')")
        with self.assertRaises(ValueError):
            replay(self.repo, "A", result["bundle_id"])

    def test_cross_tenant_archive_denied(self):
        result = ReviewService(self.catalog, self.repo).review(event(), "A")
        with self.assertRaises(LookupError):
            replay(self.repo, "B", result["bundle_id"])

    def test_obligations_survive_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "store.sqlite"
            store = SQLiteRepository(path)
            store.register_obligation(event(), "A")
            store.close()
            store = SQLiteRepository(path)
            try:
                self.assertEqual(len(store.obligations("A")), 1)
            finally:
                store.close()


@unittest.skipUnless(os.environ.get("KCCS_WORKBOOK"), "Private workbook not supplied")
class PrivateWorkbookTests(unittest.TestCase):
    def test_real_case_candidate_discovery(self):
        catalog = WorkbookCatalog(os.environ["KCCS_WORKBOOK"])
        row = next(r for r in catalog.rows("01_Excursion_Events") if r.values["event_id"] == "EXC-107133")
        result = assemble(catalog, row, row.values["tenant_code"])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any(s["source"]["values"]["study_ref"] == "STB-2738" for s in result["study_candidates"]))
        self.assertIn("SOP_REVISION_OVERLAP", result["blockers"])
