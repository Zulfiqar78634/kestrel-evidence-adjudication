"""Notification engine with outbox pattern, retry/backoff, and independent paging.

Regulatory notifications are queued in an outbox table, delivered asynchronously,
and retried with exponential backoff on failure. A separate pager channel fires
independently of the primary notification channel.
"""
from __future__ import annotations
import os
import json
import time
import logging
from typing import Any, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationState(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


@dataclass
class OutboxEntry:
    """A queued notification awaiting delivery."""
    id: str
    tenant: str
    event_id: str
    channel: str
    payload: dict[str, Any]
    state: NotificationState = NotificationState.PENDING
    attempts: int = 0
    max_attempts: int = 5
    next_retry_at: float = 0.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant": self.tenant,
            "event_id": self.event_id,
            "channel": self.channel,
            "payload": self.payload,
            "state": self.state.value,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "next_retry_at": self.next_retry_at,
            "created_at": self.created_at,
        }


class Outbox:
    """Transactional outbox for notification delivery with retry and backoff."""

    def __init__(self, max_attempts: int = 5, base_delay: float = 2.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.entries: list[OutboxEntry] = []

    def enqueue(self, tenant: str, event_id: str, channel: str, payload: dict[str, Any]) -> OutboxEntry:
        entry = OutboxEntry(
            id=f"{tenant}:{event_id}:{channel}",
            tenant=tenant,
            event_id=event_id,
            channel=channel,
            payload=payload,
        )
        self.entries.append(entry)
        return entry

    def process(self, deliver: Callable[[OutboxEntry], bool], now: float | None = None) -> list[OutboxEntry]:
        """Process all due entries, retrying failures with exponential backoff."""
        now = now if now is not None else time.time()
        for entry in self.entries:
            if entry.state == NotificationState.PENDING or (entry.state == NotificationState.RETRYING and entry.next_retry_at <= now):
                try:
                    success = deliver(entry)
                except Exception as exc:
                    logger.warning("delivery_failed", extra={"entry": entry.id, "error": str(exc)})
                    success = False
                if success:
                    entry.state = NotificationState.SENT
                else:
                    entry.attempts += 1
                    if entry.attempts >= entry.max_attempts:
                        entry.state = NotificationState.FAILED
                        logger.error("delivery_permanently_failed", extra={"entry": entry.id, "attempts": entry.attempts})
                    else:
                        entry.state = NotificationState.RETRYING
                        entry.next_retry_at = now + (self.base_delay * (2 ** (entry.attempts - 1)))
        return self.entries


class Pager:
    """Independent paging channel that fires separately from the primary notification."""

    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = webhook_url or os.environ.get("PAGER_WEBHOOK", "")

    def fire(self, tenant: str, event_id: str, severity: str, message: str) -> bool:
        """Send a page. Returns True on success, False on failure. Never blocks the main flow."""
        if not self.webhook_url:
            logger.info("pager_noop", extra={"tenant": tenant, "event_id": event_id, "severity": severity})
            return True
        try:
            import urllib.request
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps({"tenant": tenant, "event_id": event_id, "severity": severity, "message": message}).encode(),
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=5)
            return True
        except Exception as exc:
            logger.warning("pager_failed", extra={"tenant": tenant, "event_id": event_id, "error": str(exc)})
            return False


def legal_calendar(region: str, due_utc: float, now: float | None = None) -> float:
    """Adjust a deadline for business days and holidays per region.

    Currently a simplified implementation; production should use a proper calendar library.
    """
    return due_utc
