"""Tests for notification outbox, retry/backoff, and independent paging."""
import unittest
from sentinel_review.notification import Outbox, OutboxEntry, NotificationState, Pager


class TestOutbox(unittest.TestCase):
    def test_enqueue_and_process_success(self):
        outbox = Outbox()
        outbox.enqueue("T-A", "E-1", "email", {"to": "qa@example.com"})
        results = outbox.process(lambda e: True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].state, NotificationState.SENT)

    def test_retry_with_backoff(self):
        outbox = Outbox(max_attempts=3, base_delay=1.0)
        outbox.enqueue("T-A", "E-1", "email", {"to": "qa@example.com"})
        results = outbox.process(lambda e: False, now=100.0)
        self.assertEqual(results[0].state, NotificationState.RETRYING)
        self.assertEqual(results[0].attempts, 1)
        self.assertAlmostEqual(results[0].next_retry_at, 101.0)

    def test_permanent_failure_after_max_attempts(self):
        outbox = Outbox(max_attempts=2, base_delay=1.0)
        outbox.enqueue("T-A", "E-1", "email", {})
        outbox.process(lambda e: False, now=100.0)
        results = outbox.process(lambda e: False, now=200.0)
        self.assertEqual(results[0].state, NotificationState.FAILED)
        self.assertEqual(results[0].attempts, 2)


class TestPager(unittest.TestCase):
    def test_pager_noop_without_webhook(self):
        pager = Pager(webhook_url="")
        self.assertTrue(pager.fire("T-A", "E-1", "high", "test"))

    def test_pager_with_webhook(self):
        pager = Pager(webhook_url="http://localhost:9999/hook")
        result = pager.fire("T-A", "E-1", "high", "test")
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()
