"""Locust load test for Kestrel Evidence Adjudication API.

Simulates production-scale traffic: concurrent users hitting review and replay endpoints.
Run with: locust -f load_test/locustfile.py --host=http://localhost:8000
"""
from locust import HttpUser, task, between
import os
import json


class KestrelUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Authenticate once per user session."""
        self.token = os.environ.get("TEST_JWT_TOKEN", "")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(3)
    def review_case(self):
        """Review a case (highest traffic)."""
        event_id = "DEMO-1"
        self.client.post(
            f"/v1/cases/{event_id}",
            headers=self.headers,
            name="/v1/cases/[id]",
        )

    @task(2)
    def replay_case(self):
        """Replay a saved bundle."""
        bundle_id = "EVB-775add1a91c45558"
        self.client.get(
            f"/v1/cases/{bundle_id}/replay",
            headers=self.headers,
            name="/v1/cases/[id]/replay",
        )

    @task(1)
    def health_check(self):
        """Health check (lowest traffic)."""
        self.client.get("/healthz", name="/healthz")
