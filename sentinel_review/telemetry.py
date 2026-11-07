"""Live telemetry adapters for TMS, BMS, ERP, and carrier systems.

Each adapter implements a common interface for fetching raw temperature series,
shipment metadata, and batch history. Adapters are pluggable and fail-closed.
"""
from __future__ import annotations
import os
import json
import logging
from typing import Any, Protocol
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class TelemetryAdapter(Protocol):
    """Protocol for telemetry source adapters."""

    def fetch_series(self, event_id: str, tenant: str) -> list[dict[str, Any]]: ...
    def fetch_shipment(self, event_id: str, tenant: str) -> dict[str, Any]: ...
    def fetch_batch_history(self, batch_id: str, tenant: str) -> list[dict[str, Any]]: ...


@dataclass
class ThermaTraceAdapter:
    """Adapter for SYS-01 ThermaTrace Cloud Logger telemetry."""
    api_key: str = ""

    def __post_init__(self):
        self.api_key = self.api_key or os.environ.get("THERMATRACE_API_KEY", "")

    def fetch_series(self, event_id: str, tenant: str) -> list[dict[str, Any]]:
        if not self.api_key:
            raise RuntimeError("THERMATRACE_API_KEY not configured")
        # In production, this would call the ThermaTrace REST API.
        # For now, returns a stub that signals "not implemented" rather than fabricating data.
        raise NotImplementedError("ThermaTrace live adapter requires API integration")

    def fetch_shipment(self, event_id: str, tenant: str) -> dict[str, Any]:
        raise NotImplementedError("ThermaTrace live adapter requires API integration")

    def fetch_batch_history(self, batch_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("ThermaTrace live adapter requires API integration")


class CryoSenseAdapter:
    """Adapter for SYS-02 CryoSense Gateway telemetry with at-least-once delivery."""

    def fetch_series(self, event_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("CryoSense live adapter requires API integration")

    def fetch_shipment(self, event_id: str, tenant: str) -> dict[str, Any]:
        raise NotImplementedError("CryoSense live adapter requires API integration")

    def fetch_batch_history(self, batch_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("CryoSense live adapter requires API integration")


class ColdlinkAdapter:
    """Adapter for SYS-03 Coldlink BMS room/chiller alarms."""

    def fetch_series(self, event_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("Coldlink live adapter requires API integration")

    def fetch_shipment(self, event_id: str, tenant: str) -> dict[str, Any]:
        raise NotImplementedError("Coldlink live adapter requires API integration")

    def fetch_batch_history(self, batch_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("Coldlink live adapter requires API integration")


class SentinelTMSAdapter:
    """Adapter for SYS-04 Sentinel TMS shipment/leg/equipment data."""

    def fetch_series(self, event_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("SentinelTMS live adapter requires API integration")

    def fetch_shipment(self, event_id: str, tenant: str) -> dict[str, Any]:
        raise NotImplementedError("SentinelTMS live adapter requires API integration")

    def fetch_batch_history(self, batch_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("SentinelTMS live adapter requires API integration")


class ErpAdapter:
    """Adapter for SYS-05 Tenant ERP feeds (products, batches, values)."""

    def fetch_series(self, event_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("ERP live adapter requires API integration")

    def fetch_shipment(self, event_id: str, tenant: str) -> dict[str, Any]:
        raise NotImplementedError("ERP live adapter requires API integration")

    def fetch_batch_history(self, batch_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("ERP live adapter requires API integration")


class StabilityRepoAdapter:
    """Adapter for SYS-06 Stability repository (SharePoint, scans)."""

    def fetch_series(self, event_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("StabilityRepo live adapter requires API integration")

    def fetch_shipment(self, event_id: str, tenant: str) -> dict[str, Any]:
        raise NotImplementedError("StabilityRepo live adapter requires API integration")

    def fetch_batch_history(self, batch_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("StabilityRepo live adapter requires API integration")


class DocuvaultAdapter:
    """Adapter for SYS-07 Docuvault controlled SOPs."""

    def fetch_series(self, event_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("Docuvault live adapter requires API integration")

    def fetch_shipment(self, event_id: str, tenant: str) -> dict[str, Any]:
        raise NotImplementedError("Docuvault live adapter requires API integration")

    def fetch_batch_history(self, batch_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("Docuvault live adapter requires API integration")


class ContractRepoAdapter:
    """Adapter for SYS-08 Contract repository (contracts, amendments)."""

    def fetch_series(self, event_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("ContractRepo live adapter requires API integration")

    def fetch_shipment(self, event_id: str, tenant: str) -> dict[str, Any]:
        raise NotImplementedError("ContractRepo live adapter requires API integration")

    def fetch_batch_history(self, batch_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("ContractRepo live adapter requires API integration")


class CarrierAdapter:
    """Adapter for SYS-09 Carrier interfaces (REST, EDI, email CSV, fax)."""

    def fetch_series(self, event_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("Carrier live adapter requires API integration")

    def fetch_shipment(self, event_id: str, tenant: str) -> dict[str, Any]:
        raise NotImplementedError("Carrier live adapter requires API integration")

    def fetch_batch_history(self, batch_id: str, tenant: str) -> list[dict[str, Any]]:
        raise NotImplementedError("Carrier live adapter requires API integration")
