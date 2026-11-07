"""Regression tests for defects found in the engineering review (docs/REVIEW.md)."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from openpyxl import Workbook
import sentinel_review
from sentinel_review import assembly
from sentinel_review.assembly import FrozenCatalog, assemble
from sentinel_review.demo import build_demo_workbook
from sentinel_review.domain import SourceRow, serialized
from sentinel_review.service import ReviewService, replay
from sentinel_review.storage import SQLiteRepository
from sentinel_review.workbook import REQUIRED, WorkbookCatalog
from test_review import MemoryCatalog, event

ROOT = Path(__file__).resolve().parents[1]


def rejections(catalog):
    return [s["discovery_rejections"] for s in assemble(catalog, event(), "A")["study_candidates"]]


class PresentationWordTests(unittest.TestCase):
    def setUp(self):
        self.catalog = MemoryCatalog()
        self.product = self.catalog.tables["02_Product_Master"][0].values
        self.study = self.catalog.tables["06_Stability_Index"][0].values

    def test_pen_inside_another_word_is_not_a_pen(self):
        self.product["brand_as_labelled"] = "Penicillin Depot"
        self.study["product_text_as_written"] = "Penicillin Depot vial"
        self.assertNotIn("PRESENTATION_CONFLICT", rejections(self.catalog)[0])

    def test_a_real_pen_still_conflicts_with_a_vial_study(self):
        self.product["brand_as_labelled"] = "Demo Pen 100U"
        self.study["product_text_as_written"] = "Demo Pen 100U vial"
        self.assertIn("PRESENTATION_CONFLICT", rejections(self.catalog)[0])

    def test_solojet_counts_as_a_pen(self):
        self.product["brand_as_labelled"] = "Demo SoloJet 100U"
        self.study["product_text_as_written"] = "Demo SoloJet 100U vial"
        self.assertIn("PRESENTATION_CONFLICT", rejections(self.catalog)[0])

    def test_vial_inside_another_word_is_not_a_vial(self):
        self.product["brand_as_labelled"] = "Demo Pen 100U"
        self.study["product_text_as_written"] = "Demo Pen 100U trivial note"
        self.assertNotIn("PRESENTATION_CONFLICT", rejections(self.catalog)[0])


class WorkbookShapeTests(unittest.TestCase):
    def test_empty_sheet_is_a_clear_value_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.xlsx"
            book = Workbook()
            book.remove(book.active)
            for name in sorted(REQUIRED):
                book.create_sheet(name)
            book.save(path)
            with self.assertRaises(ValueError):
                WorkbookCatalog(path)


class CatalogContractTests(unittest.TestCase):
    def test_frozen_catalog_reports_unknown_sheet_like_the_workbook_adapter(self):
        with self.assertRaises(ValueError):
            FrozenCatalog({"tables": {}}).rows("nope")


class SnapshotTests(unittest.TestCase):
    def build(self, extra):
        catalog = MemoryCatalog()
        for i in range(extra):
            catalog.tables["02_Product_Master"].append(SourceRow("02_Product_Master", 10 + i, {
                "tenant_code": "A", "gtin": f"9{i:013d}", "brand_as_labelled": f"Other {i}"}))
            catalog.tables["06_Stability_Index"].append(SourceRow("06_Stability_Index", 10 + i, {
                "tenant_code": "A", "study_ref": f"X{i}", "product_text_as_written": f"Unrelated {i}",
                "study_type": "Excursion", "readable": "Y", "permitted_excursion_text": "n/a"}))
            catalog.tables["05_SOP_Index"].append(SourceRow("05_SOP_Index", 10 + i, {
                "tenant_code": "A", "doc_id": f"C{i}", "title": "Cleaning", "effective_from": "2025-01-01"}))
        repo = SQLiteRepository(":memory:")
        self.addCleanup(repo.close)
        saved = ReviewService(catalog, repo).review(event(), "A")
        return repo, saved

    def test_snapshot_keeps_only_rows_that_were_used(self):
        repo, saved = self.build(extra=30)
        payload = repo.read("A", saved["bundle_id"])
        counts = {name: len(rows) for name, rows in payload["captured"]["tables"].items()}
        self.assertEqual(counts, {"02_Product_Master": 1, "05_SOP_Index": 1, "06_Stability_Index": 1})

    def test_snapshot_size_does_not_grow_with_unrelated_rows(self):
        small = len(serialized(self.build(extra=0)[0].read("A", self.build(extra=0)[1]["bundle_id"])))
        repo, saved = self.build(extra=200)
        self.assertEqual(len(serialized(repo.read("A", saved["bundle_id"]))), small)

    def test_trimmed_snapshot_still_replays_identically(self):
        repo, saved = self.build(extra=30)
        self.assertTrue(replay(repo, "A", saved["bundle_id"])["identical"])


class VersionTests(unittest.TestCase):
    def test_package_evaluator_and_pyproject_versions_agree(self):
        declared = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.M).group(1)
        self.assertEqual(sentinel_review.__version__, assembly.VERSION)
        self.assertEqual(sentinel_review.__version__, declared)


class CliSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workbook = Path(self.temp.name) / "demo.xlsx"
        self.db = str(Path(self.temp.name) / "demo.sqlite")
        self.out = Path(self.temp.name) / "out.json"
        build_demo_workbook(self.workbook)

    def cli(self, *args):
        return subprocess.run([sys.executable, "-m", "sentinel_review.cli", "--db", self.db, *args],
                              cwd=ROOT, capture_output=True, text=True, timeout=60)

    def test_review_without_tenant_is_refused_unless_all_tenants_is_explicit(self):
        refused = self.cli("review", str(self.workbook), "--out", str(self.out))
        self.assertNotEqual(refused.returncode, 0)
        self.assertFalse(self.out.exists())
        allowed = self.cli("review", str(self.workbook), "--all-tenants", "--out", str(self.out))
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertEqual(len(json.loads(self.out.read_text())), 3)

    def test_wrong_tenant_replay_fails_cleanly(self):
        self.cli("review", str(self.workbook), "--event", "DEMO-1", "--tenant", "T-DEMO-A", "--out", str(self.out))
        bundle = json.loads(self.out.read_text())[0]["bundle_id"]
        denied = self.cli("replay", bundle, "--tenant", "T-DEMO-B")
        self.assertEqual(denied.returncode, 2)
        self.assertEqual(json.loads(denied.stderr)["error"], "LookupError")
        self.assertNotIn("Traceback", denied.stderr)
        self.assertEqual(denied.stdout, "")


if __name__ == "__main__":
    unittest.main()
