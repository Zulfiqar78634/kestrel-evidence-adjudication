"""Tests for WORM archive write-once semantics and retention verification."""
import unittest
import tempfile
import shutil
from pathlib import Path
from sentinel_review.archive import WormArchive


class TestWormArchive(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.archive = WormArchive(base_dir=self.tmpdir, retention_years=7)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_write_once(self):
        payload = {"event_id": "E-1", "data": "test"}
        path = self.archive.write("T-A", "E-1", payload)
        self.assertTrue(Path(path).exists())
        with self.assertRaises(FileExistsError):
            self.archive.write("T-A", "E-1", payload)

    def test_read_back(self):
        payload = {"event_id": "E-1", "data": "test"}
        self.archive.write("T-A", "E-1", payload)
        result = self.archive.read("T-A", "E-1")
        self.assertIsNotNone(result)
        self.assertEqual(result["event_id"], "E-1")

    def test_retention_check(self):
        payload = {"event_id": "E-1", "created_at": 0}
        self.archive.write("T-A", "E-1", payload)
        self.assertTrue(self.archive.verify_retention("T-A", "E-1", now=1000000))
        self.assertFalse(self.archive.verify_retention("T-A", "E-1", now=999999999999))


if __name__ == "__main__":
    unittest.main()
