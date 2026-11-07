"""Mock telemetry adapters for local testing and CI without real API keys.

Each adapter returns deterministic synthetic data derived from the event_id hash,
so tests are reproducible and no external API is needed.
"""
from __future__ import annotations
import hashlib
import json
from typing import Any
from .telemetry import ThermaTraceAdapter, CryoSenseAdapter, ColdlinkAdapter, SentinelTMSAdapter, ErpAdapter, StabilityRepoAdapter, DocuvaultAdapter, ContractRepoAdapter, CarrierAdapter


class MockTelemetryAdapter:
    """Base class for mock adapters. Generates deterministic data from event_id hash."""

    def _seed(self, event_id: str, tenant: str) -> int:
        return int(hashlib.sha256(f"{tenant}:{event_id}".encode()).hexdigest()[:8], 16)

    def fetch_series(self, event_id: str, tenant: str) -> list[dict[str, Any]]:
        seed = self._seed(event_id, tenant)
        return [{"ts": i, "temp_c": 2.0 + (seed % 100) / 10.0} for i in range(4)]

    def fetch_shipment(self, event_id: str, tenant: str) -> dict[str, Any]:
        seed = self._seed(event_id, tenant)
        return {"shipment_id": f"SHP-{seed}", "leg": 1, "carrier": "MockCarrier"}

    def fetch_batch_history(self, batch_id: str, tenant: str) -> list[dict[str, Any]]:
        seed = self._seed(batch_id, tenant)
        return [{"batch_id": batch_id, "prior_excursions": seed % 3}]


class MockThermaTraceAdapter(MockTelemetryAdapter, ThermaTraceAdapter):
    pass


class MockCryoSenseAdapter(MockTelemetryAdapter, CryoSenseAdapter):
    pass


class MockColdlinkAdapter(MockTelemetryAdapter, ColdlinkAdapter):
    pass


class MockSentinelTMSAdapter(MockTelemetryAdapter, SentinelTMSAdapter):
    pass


class MockErpAdapter(MockTelemetryAdapter, ErpAdapter):
    pass


class MockStabilityRepoAdapter(MockTelemetryAdapter, StabilityRepoAdapter):
    pass


class MockDocuvaultAdapter(MockTelemetryAdapter, DocuvaultAdapter):
    pass


class MockContractRepoAdapter(MockTelemetryAdapter, ContractRepoAdapter):
    pass


class MockCarrierAdapter(MockTelemetryAdapter, CarrierAdapter):
    pass
