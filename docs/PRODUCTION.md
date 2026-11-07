# Production Readiness Guide

## What is production-ready now

| Capability | Status | How to verify |
|---|---|---|
| JWT authentication with tenant claim | Implemented | `POST /v1/cases/{id}` with Bearer token; wrong tenant returns 403 |
| Role-based access (viewer/reviewer/admin) | Implemented | `Principal.can(role)` hierarchy enforced |
| PostgreSQL adapter | Implemented | `PostgresRepository` with SQLAlchemy async, connection pooling, transactional writes |
| Docker multi-stage build | Implemented | `docker build -t kestrel .` succeeds; non-root user; HEALTHCHECK |
| CI pipeline | Implemented | `.github/workflows/ci.yml` runs ruff, mypy, pytest with coverage, Docker build |
| Health/readiness probes | Implemented | `/healthz` (liveness) and `/readyz` (readiness) return 200 |
| Structured logging | Implemented | `logging.basicConfig` with tenant, event_id, user context |
| Task closure with approved evidence | Implemented | `ResolutionTask` requires evidence hash; blank transcription never clears blocker |
| Notification outbox with retry/backoff | Implemented | `Outbox.process` with exponential backoff, permanent failure after max attempts |
| Independent pager channel | Implemented | `Pager.fire` fires separately from primary notification, never blocks main flow |
| WORM archive (local fallback) | Implemented | `WormArchive.write` is append-only, raises on rewrite; retention verification built in |
| Telemetry adapter interfaces | Implemented | 9 adapters defined, all fail-closed (raise NotImplementedError until real integration) |
| Mock telemetry adapters (deterministic) | Implemented | `MockTelemetryAdapter` generates deterministic data from event_id hash, no external API needed |
| Mock notification providers (email/SMS/pager) | Implemented | `MockEmailProvider`, `MockSmsProvider`, `MockPagerProvider` log instead of send, no external API needed |
| Mock WORM archive (in-memory) | Implemented | `MockWormArchive` uses in-memory dict, write-once semantics enforced |
| End-to-end integration test | Implemented | `test_full_flow_mock` verifies enqueue -> dispatch -> SENT state |
| Load testing (Locust) | Implemented | `load_test/locustfile.py` simulates concurrent users on review/replay/health endpoints |
| Chaos engineering (network/DB/provider failure) | Implemented | `load_test/chaos.py` simulates network, DB, notification provider, telemetry failures |
| Local verification script | Implemented | `load_test/verify_local.sh` runs full end-to-end verification in one command |

## What is still deferred

| Capability | Status | Why |
|---|---|---|
| Real notification delivery (email/SMS/pager) | Deferred | Requires external provider integration (SendGrid, Twilio, PagerDuty) |
| Immutable archive (S3 Object Lock / Azure Immutable Blob) | Deferred | Requires cloud storage backend integration |
| Qualified e-signature (21 CFR Part 11) | Deferred | Requires identity provider integration and audit trail certification |
| Live telemetry ingestion (TMS, BMS, ERP) | Deferred | Requires real-time adapters to 9 source systems |
| Production-scale load test (real traffic) | Deferred | Requires production-scale traffic simulation with real data |

## Local verification (no private data, no API keys needed)

```bash
# One-command verification
bash load_test/verify_local.sh

# Or step by step
git clone https://github.com/Zulfiqar78634/kestrel-evidence-adjudication.git
cd kestrel-evidence-adjudication
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v          # 70+ tests pass
python -m sentinel_review.demo demo.xlsx
sentinel-review --db demo.sqlite review demo.xlsx --event DEMO-1 --tenant T-DEMO-A --out demo-case.json
sentinel-review --db demo.sqlite replay BUNDLE_ID --tenant T-DEMO-A
python -m unittest load_test.chaos -v            # chaos tests pass
```

## Production deployment (Docker Compose)

```bash
docker compose up --build
# App runs on http://localhost:8000
# Health: curl http://localhost:8000/healthz
# Ready: curl http://localhost:8000/readyz
# Review a case: curl -X POST -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/cases/EXC-107133
```

## Load testing (Locust)

```bash
pip install locust
locust -f load_test/locustfile.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 30s
# Simulates 10 concurrent users, 2 users/sec ramp, 30 second duration
```

## Chaos engineering

```bash
python -m unittest load_test.chaos -v
# Tests: network failure, DB failure, notification provider failure, telemetry failure
# All scenarios verify fail-closed behavior and graceful degradation
```

## CI verification

Push to `main` triggers `.github/workflows/ci.yml`:
1. `ruff check sentinel_review` — lint gate
2. `mypy sentinel_review` — type gate
3. `coverage run -m unittest discover -s tests` + `coverage report --fail-under=80` — test gate
4. `docker build` — container gate

All four gates must pass for a green build.

## How to swap mock for real providers

| Component | Mock (local/CI) | Real (production) |
|---|---|---|
| Telemetry | `MockTelemetryAdapter` | `ThermaTraceAdapter` etc. with API key |
| Email | `MockEmailProvider` | SendGrid API key |
| SMS | `MockSmsProvider` | Twilio API key |
| Pager | `MockPagerProvider` | PagerDuty integration key |
| Archive | `MockWormArchive` | S3 Object Lock / Azure Immutable Blob |

Swap is a one-line change in the service constructor.
