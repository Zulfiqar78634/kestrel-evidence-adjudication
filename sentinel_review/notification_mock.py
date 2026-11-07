"""Mock notification providers for local testing and CI without real API keys.

Uses in-memory delivery simulation. For production, swap in SendGrid/Twilio/PagerDuty.
"""
from __future__ import annotations
import logging
from typing import Any
from .notification import Outbox, OutboxEntry, NotificationState

logger = logging.getLogger(__name__)


class MockEmailProvider:
    """Mock email provider. Logs the payload instead of sending."""

    def send(self, to: str, subject: str, body: str) -> bool:
        logger.info("mock_email_sent", extra={"to": to, "subject": subject})
        return True


class MockSmsProvider:
    """Mock SMS provider. Logs the payload instead of sending."""

    def send(self, to: str, body: str) -> bool:
        logger.info("mock_sms_sent", extra={"to": to})
        return True


class MockPagerProvider:
    """Mock pager provider. Logs the payload instead of sending."""

    def send(self, severity: str, message: str) -> bool:
        logger.info("mock_pager_sent", extra={"severity": severity, "message": message})
        return True


class NotificationDispatcher:
    """Dispatches notifications via the appropriate mock provider."""

    def __init__(self):
        self.email = MockEmailProvider()
        self.sms = MockSmsProvider()
        self.pager = MockPagerProvider()

    def dispatch(self, entry: OutboxEntry) -> bool:
        """Route the entry to the correct mock provider based on channel."""
        if entry.channel == "email":
            return self.email.send(entry.payload.get("to", ""), entry.payload.get("subject", ""), entry.payload.get("body", ""))
        elif entry.channel == "sms":
            return self.sms.send(entry.payload.get("to", ""), entry.payload.get("body", ""))
        elif entry.channel == "pager":
            return self.pager.send(entry.payload.get("severity", ""), entry.payload.get("message", ""))
        return False
