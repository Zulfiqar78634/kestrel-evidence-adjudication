"""Use cases. Dependencies are injected ports; obligation admission precedes assembly."""
from .assembly import VERSION, FrozenCatalog, assemble, snapshot
from .domain import SourceRow
from .ports import EvidenceRepository, SourceCatalog


class ReviewService:
    def __init__(self, catalog: SourceCatalog, repository: EvidenceRepository):
        self.catalog, self.repository = catalog, repository

    def review(self, event: SourceRow, tenant: str):
        self.repository.register_obligation(event, tenant)
        result = assemble(self.catalog, event, tenant)
        payload = {"version": VERSION, "captured": snapshot(self.catalog, event, tenant), "result": result}
        return {"bundle_id": self.repository.save(tenant, payload), "result": result}


def replay(repository: EvidenceRepository, tenant: str, key: str):
    payload = repository.read(tenant, key)
    if payload["version"] != VERSION:
        raise ValueError("archived evaluator unavailable")
    captured = payload["captured"]
    row = captured["event"]
    result = assemble(FrozenCatalog(captured), SourceRow(row["sheet"], row["row"], row["values"]), tenant)
    if result != payload["result"]:
        raise ValueError("replay divergence")
    return {"bundle_id": key, "identical": True, "result": result}
