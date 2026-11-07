"""Tests for mock telemetry adapters (deterministic, no external API)."""
import unittest
from sentinel_review.telemetry_mock import MockThermaTraceAdapter, MockCryoSenseAdapter, MockColdlinkAdapter, MockSentinelTMSAdapter, MockErpAdapter, MockStabilityRepoAdapter, MockDocuvaultAdapter, MockContractRepoAdapter, MockCarrierAdapter


class TestMockTelemetry(unittest.TestCase):
    def test_all_mock_adapters_deterministic(self):
        adapters = [MockThermaTraceAdapter(), MockCryoSenseAdapter(), MockColdlinkAdapter(), MockSentinelTMSAdapter(), MockErpAdapter(), MockStabilityRepoAdapter(), MockDocuvaultAdapter(), MockContractRepoAdapter(), MockCarrierAdapter()]
        for adapter in adapters:
            series1 = adapter.fetch_series("E-1", "T-A")
            series2 = adapter.fetch_series("E-1", "T-A")
            self.assertEqual(series1, series2)
            self.assertEqual(len(series1), 4)

    def test_shipment_and_batch(self):
        adapter = MockThermaTraceAdapter()
        shipment = adapter.fetch_shipment("E-1", "T-A")
        self.assertIn("shipment_id", shipment)
        batch = adapter.fetch_batch_history("B-1", "T-A")
        self.assertIn("batch_id", batch)


if __name__ == "__main__":
    unittest.main()
