"""Tests for telemetry adapter fail-closed behavior."""
import unittest
from sentinel_review.telemetry import ThermaTraceAdapter, CryoSenseAdapter, ColdlinkAdapter, SentinelTMSAdapter, ErpAdapter, StabilityRepoAdapter, DocuvaultAdapter, ContractRepoAdapter, CarrierAdapter


class TestTelemetryAdapters(unittest.TestCase):
    def test_all_adapters_fail_closed(self):
        adapters = [ThermaTraceAdapter(), CryoSenseAdapter(), ColdlinkAdapter(), SentinelTMSAdapter(), ErpAdapter(), StabilityRepoAdapter(), DocuvaultAdapter(), ContractRepoAdapter(), CarrierAdapter()]
        for adapter in adapters:
            with self.assertRaises((NotImplementedError, RuntimeError)):
                adapter.fetch_series("E-1", "T-A")


if __name__ == "__main__":
    unittest.main()
