# Executive System Architecture & Regulatory Compliance Position

## 1. Executive Summary & Purpose
Kestrel provides critical cold-chain custody logistics for pharmaceutical manufacturers. The core commercial deliverable is not merely freight transit; it is the **defensible custody and compliance evidence** required by a Qualified Person (QP) or licensed pharmacist to release temperature-sensitive medicines.

This platform automates evidence compilation, candidate discovery, and conflict detection. It explicitly **refuses autonomous product disposition decisions** (release or destruction) whenever governing authority or source evidence is missing.

---

## 2. SOLID Architectural Principles in Practice

The implementation adheres to SOLID engineering principles:

```
┌──────────────────────────────────────────────────────────────────┐
│                   Domain Core (Single Responsibility)             │
│   • ExcursionEvent, ResolutionTask, TenantScope                  │
│   • Pure validation, deterministic hashing, zero network/IO       │
└─────────────────────────────────┬────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────┐
│               Ports / Interfaces (Dependency Inversion)          │
│   • SourceCatalog: Abstract data retrieval                       │
│   • EvidenceRepository: Abstract immutable persistence           │
└──────────────────┬───────────────────────────────┬───────────────┘
                   │                               │
┌──────────────────▼───────────────┐ ┌─────────────▼───────────────┐
│     Adapters (Liskov Sub)        │ │    Adapters (Extensible)    │
│   • SQLiteRepository             │ │   • WorkbookCatalog         │
│   • PostgresRepository (Target)  │ │   • LiveTMSCatalog (Target) │
└──────────────────────────────────┘ └─────────────────────────────┘
```

1. **Single Responsibility Principle (SRP):**  
   - `domain.py`: Pure immutable types, GTIN/timestamp normalization, cryptographic SHA-256 digests. Zero disk or network I/O.
   - `tasks.py`: Deterministic task generator mapping unverified blockers to responsible functional roles.
   - `assembly.py`: Pipeline connecting raw alerts to discovered candidates and conflict blockers.
   - `storage.py`: Content-addressed bundle storage and separate regulatory clock state.
2. **Open/Closed Principle (OCP):**  
   - The engine evaluates rules and blockers through modular lookup tables. New stability rejections or validation checks can be registered without mutating core storage or service logic.
3. **Liskov Substitution Principle (LSP):**  
   - Any `SourceCatalog` implementation (`WorkbookCatalog`, `FrozenCatalog`, or in-memory fixtures) behaves identically: missing sheets predictably raise `ValueError`, and rows are provided as immutable `SourceRow` instances.
4. **Interface Segregation Principle (ISP):**  
   - Client code interacts with narrow protocols defined in `ports.py` rather than tightly coupled database drivers.
5. **Dependency Inversion Principle (DIP):**  
   - `ReviewService` depends strictly on `SourceCatalog` and `EvidenceRepository` abstractions. Storage adapters and Excel parsers are injected at runtime.

---

## 3. Regulatory Invariants & Data Governance

| Invariant | System Guarantee | GxP / Regulatory Justification |
|---|---|---|
| **Fail-Closed Disposition** | Every result is marked `BLOCKED` with `final_disposition = null`. | 21 CFR Part 11; EU Annex 11. AI models and lexical searches lack legal release authority. |
| **Independent Regulatory Clock** | Regulatory obligations are persisted before case assembly. | 21 CFR 314.81; WHO TRS 961. Health authority deviation reporting deadlines (e.g. 72 hours) run independently of product release holds. |
| **Tamper-Evident Replay** | Every bundle is keyed by its SHA-256 content digest. | ALCOA+ audit trail integrity. Replaying saved bundles verifies that input data has not drifted. |
| **Multi-Tenant Isolation** | Scoping checks run at all entry points; bundles are keyed by `(tenant, id)`. | Protects commercial confidentiality across enterprise pharmaceutical customers. |

---

## 4. The EXC-107133 Case Study Benchmark

* **The Alert:** 15-minute excursion reaching 11.2°C for Glucodyne SoloJet 100U insulin during transit between Bhiwandi Hub and Kundli Pharma Store. Label storage: 2.0°C–8.0°C.
* **Discovered Evidence:**
  - Product Master row 57 cites `STB-3584`.
  - `STB-3584` is an unreadable/accelerated study conducted on vials, not SoloJet pens (`PRESENTATION_CONFLICT`).
  - Study `STB-2738` exists for pens ("One excursion, up to 6 h below 15 °C"), but the Product Master claims "Cumulative 72 h above 8 °C".
  - Two overlapping SOP revisions (`Rev 02` and `Rev 03`) exist for the excursion date.
* **Engine Response:**
  - Emits 10 discrete **Resolution Tasks** assigning specific investigation actions to Document Control, Stability Study Owners, and Site QA.
  - Registers the regulatory notification obligation.
  - Refuses automated release, locking state in `BLOCKED`.
