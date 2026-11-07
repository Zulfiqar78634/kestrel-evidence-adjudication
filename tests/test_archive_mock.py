"""Tests for mock WORM archive (in-memory, no cloud storage needed)."""
import unittest
from sentinel_review.archive_mock import MockWormArchive


class TestMockWormArchive(unittest.TestCase):
    def test_write_once(self):
        archive = MockWormArchive()
        payload = {"event_id": "E-1", "data": "test"}
        key = archive.write("T-A", "E-1", payload)
        self.assertIn(key, archive.store)
        with self.assertRaises(FileExistsError):
            archive.write("T-A", "E-1", payload)

    def test_read_back(self):
        archive = MockWormArchive()
        payload = {"event_id": "E-1", "data": "test"}
        archive.write("T-A", "E-1", payload)
        result = archive.read("T-A", "E-1")
        self.assertIsNotNone(result)
        self.assertEqual(result["event_id"], "E-1")

    def test_retention_check(self):
        archive = MockWormArchive()
        payload = {"event_id": "E-1", "created_at": 0}
        archive.write("T-A", "E-1", payload)
        self.assertTrue(archive.verify_retention("T-A", "E-1", now=1000000))
        self.assertFalse(archive.verify_retention("T-A", "E-1", now=999999999999))


if __name__ == "__main__":
    unittest.main()
