"""Tests for mock notification providers (no external API needed)."""
import unittest
from sentinel_review.notification_mock import MockEmailProvider, MockSmsProvider, MockPagerProvider, NotificationDispatcher
from sentinel_review.notification import Outbox, OutboxEntry


class TestMockProviders(unittest.TestCase):
    def test_email_mock(self):
        provider = MockEmailProvider()
        self.assertTrue(provider.send("qa@example.com", "Test", "Body"))

    def test_sms_mock(self):
        provider = MockSmsProvider()
        self.assertTrue(provider.send("+1234567890", "Test"))

    def test_pager_mock(self):
        provider = MockPagerProvider()
        self.assertTrue(provider.send("high", "Test"))

    def test_dispatcher_routes_correctly(self):
        dispatcher = NotificationDispatcher()
        entry = OutboxEntry(id="1", tenant="T-A", event_id="E-1", channel="email", payload={"to": "qa@example.com", "subject": "Test", "body": "Body"})
        self.assertTrue(dispatcher.dispatch(entry))


class TestEndToEnd(unittest.TestCase):
    def test_full_flow_mock(self):
        """End-to-end: enqueue notification, dispatch via mock, verify state."""
        outbox = Outbox()
        dispatcher = NotificationDispatcher()
        outbox.enqueue("T-A", "E-1", "email", {"to": "qa@example.com", "subject": "Test", "body": "Body"})
        results = outbox.process(dispatcher.dispatch)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].state.value, "SENT")


if __name__ == "__main__":
    unittest.main()
