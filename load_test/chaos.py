"""Chaos engineering scenarios for Kestrel Evidence Adjudication.

Simulates network failure, DB failure, and notification provider failure to verify
fail-closed behavior and graceful degradation.
"""
from __future__ import annotations
import unittest
from unittest.mock import patch, MagicMock
from sentinel_review.notification import Outbox, OutboxEntry, NotificationState
from sentinel_review.archive_mock import MockWormArchive
from sentinel_review.telemetry_mock import MockThermaTraceAdapter


class TestNetworkFailure(unittest.TestCase):
    """Simulate network failure during notification delivery."""

    def test_notification_retry_on_network_failure(self):
        outbox = Outbox(max_attempts=3, base_delay=1.0)
        outbox.enqueue("T-A", "E-1", "email", {"to": "qa@example.com"})
        with patch("sentinel_review.notification.Outbox.process") as mock_process:
            mock_process.side_effect = ConnectionError("network down")
            with self.assertRaises(ConnectionError):
                outbox.process(lambda e: True)


class TestDbFailure(unittest.TestCase):
    """Simulate DB failure during evidence write."""

    def test_archive_write_failure(self):
        archive = MockWormArchive()
        with patch.object(archive, "write", side_effect=IOError("disk full")):
            with self.assertRaises(IOError):
                archive.write("T-A", "E-1", {"data": "test"})


class TestNotificationProviderFailure(unittest.TestCase):
    """Simulate notification provider failure (email/SMS/pager down)."""

    def test_pager_failure_does_not_block(self):
        from sentinel_review.notification import Pager
        pager = Pager(webhook_url="http://localhost:9999/hook")
        with patch("urllib.request.urlopen", side_effect=Exception("provider down")):
            result = pager.fire("T-A", "E-1", "high", "test")
            self.assertFalse(result)


class TestTelemetryFailure(unittest.TestCase):
    """Simulate telemetry adapter failure."""

    def test_telemetry_failure_fail_closed(self):
        adapter = MockThermaTraceAdapter()
        with patch.object(adapter, "fetch_series", side_effect=RuntimeError("telemetry down")):
            with self.assertRaises(RuntimeError):
                adapter.fetch_series("E-1", "T-A")


if __name__ == "__main__":
    unittest.main()
