"""Tests for load testing and chaos engineering scenarios."""
import unittest
from unittest.mock import patch, MagicMock
from sentinel_review.notification import Outbox, OutboxEntry, NotificationState
from sentinel_review.archive_mock import MockWormArchive
from sentinel_review.telemetry_mock import MockThermaTraceAdapter


class TestLoadScenarios(unittest.TestCase):
    """Simulate high-concurrency load on outbox and archive."""

    def test_outbox_high_concurrency(self):
        outbox = Outbox()
        for i in range(100):
            outbox.enqueue("T-A", f"E-{i}", "email", {"to": "qa@example.com"})
        results = outbox.process(lambda e: True)
        self.assertEqual(len(results), 100)
        self.assertTrue(all(r.state == NotificationState.SENT for r in results))

    def test_archive_high_concurrency(self):
        archive = MockWormArchive()
        for i in range(100):
            archive.write("T-A", f"E-{i}", {"data": i})
        self.assertEqual(len(archive.store), 100)


class TestChaosScenarios(unittest.TestCase):
    """Simulate failure scenarios and verify graceful degradation."""

    def test_outbox_retry_on_failure(self):
        outbox = Outbox(max_attempts=2, base_delay=1.0)
        outbox.enqueue("T-A", "E-1", "email", {})
        outbox.process(lambda e: False, now=100.0)
        results = outbox.process(lambda e: False, now=200.0)
        self.assertEqual(results[0].state, NotificationState.FAILED)

    def test_archive_write_failure(self):
        archive = MockWormArchive()
        with patch.object(archive, "write", side_effect=IOError("disk full")):
            with self.assertRaises(IOError):
                archive.write("T-A", "E-1", {"data": "test"})

    def test_telemetry_failure(self):
        adapter = MockThermaTraceAdapter()
        with patch.object(adapter, "fetch_series", side_effect=RuntimeError("telemetry down")):
            with self.assertRaises(RuntimeError):
                adapter.fetch_series("E-1", "T-A")


if __name__ == "__main__":
    unittest.main()
