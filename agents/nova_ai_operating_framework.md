# Nova AI Operating Framework (Sunlight Doctrine)

## 1) Why this exists
Keep all agents aligned with Nova's epistemology: slots interpret, core attests, everything observable & reversible.

## 2) Mental model (quick)

**Rule of Sunlight:** Observe → Canonize → Attest → Publish.

**Three Ledgers:**
- Fact ledger (raw observations, append-only)
- Claim ledger (slot outputs with assumptions + confidence)
- Attest ledger (hash-linked, optionally signed events, tamper-evident)

**Invariants:** separation, provenance, immutability, reversibility, uncertainty, observability.

## 3) First 10 minutes checklist

**Read:**
- `src/nova/slots/*/meta.yaml` (legacy shims remain under `slots/`)
- `orchestrator/app.py`
- `orchestrator/prometheus_metrics.py`
- `src/nova/slots/slot07_production_controls/flag_metrics.py`

**Run:**
- `pytest -q -m "not slow"`
- Then targeted lanes for any flag you touch

**Verify:**
- `/metrics` when `NOVA_ENABLE_PROMETHEUS=1`

## 4) Capability probes (self-diagnostics)

**TRI↔Constellation:**
- `NOVA_ENABLE_TRI_LINK=1`
- `pytest tests/e2e/test_constellation_with_tri.py`

**Lifespan:**
- `NOVA_ENABLE_LIFESPAN=1`
- `pytest tests/web/test_lifespan.py`

**Shared Hash:**
- `NOVA_USE_SHARED_HASH=1`
- `pytest tests/test_slot09_shared_hash_coverage.py::test_audit_hash_chain_with_shared_hash_enabled`

**Observability:**
- `NOVA_ENABLE_PROMETHEUS=1`
- `pytest tests/web/test_prometheus_route.py`

**Slot1 Truth Anchors:**
- `pytest tests/test_slot1_enhanced_adapter.py`
- `pytest tests/web/test_prometheus_slot1.py`

## 5) Change policy

- **Off-by-default, flag-gated, reversible**
- Add tests + CI matrix entries + meta flag docs
- No touching compiled artifacts or large refactors without flags
- Commitlint-compliant messages
- Prometheus metrics follow `nova_slotN_*` naming convention

## 6) Attestation rules

- Shared blake2b when available & enabled; otherwise sha256
- Include `hash_method`, link `prev`, sign when RealityLock is present
- Deterministic canonicalization before hashing
- Truth anchors use persistent storage with atomic writes

## 7) Observability

- Export key metrics (e.g., Slot6 `p95_residual_risk`, flag gauges, Slot1 anchor counts)
- Keep `/metrics` gated; provide fallbacks; no stale values
- Use dedicated Prometheus registry to avoid conflicts

## 8) Common pitfalls

- Reading env only at import time (fix: re-read at call-time)
- Ungated behavior changes
- Tests that assume specific content-type versions (assert prefix/suffix instead)
- Overwriting history (append-only; corrections are new events)
- Breaking backward compatibility without graceful degradation

## 9) When in doubt

- Prefer the smallest diff that increases sunlight (provenance, metrics, tests)
- State assumptions; show rollback path
- Surface disagreement rather than forcing consensus
- Choose reversible steps and instrument them
- Honor the separation: slots interpret, core attests

## 10) Feature flag reference (source of truth)

| Flag                   | Purpose                                   | Default | Targeted test lane                                             | Exposed metric                               |
|------------------------|--------------------------------------------|---------|-----------------------------------------------------------------|----------------------------------------------|
| NOVA_ENABLE_TRI_LINK   | TRI ↔ Constellation integration            | Off     | `tests/e2e/test_constellation_with_tri.py`                      | `nova_feature_flag_enabled{flag="..."}==1`   |
| NOVA_ENABLE_LIFESPAN   | FastAPI lifespan manager                   | Off     | `tests/web/test_lifespan.py`                                    | `nova_feature_flag_enabled{flag="..."}==1`   |
| NOVA_USE_SHARED_HASH   | Use shared blake2b for audit chains        | Off     | `tests/test_slot09_shared_hash_coverage.py::test_*shared*`      | `nova_feature_flag_enabled{flag="..."}==1`   |
| NOVA_ENABLE_PROMETHEUS | Enable `/metrics` Prometheus export        | Off     | `tests/web/test_prometheus_route.py`                            | `nova_feature_flag_enabled{flag="..."}==1`   |

**Notes**
- Flags are re-read at **call-time**; never cache only at import.
- When shared hash is enabled & available → `hash_method="shared_blake2b"`; else `fallback_sha256`.

## 11) Pre-merge checklist (CI-green, sunlight-safe)

- [ ] **Commitlint**: Conventional Commits; wrap body lines ≤100 chars.
- [ ] **Tests**: `pytest -q -m "not slow"` passes locally.
- [ ] **Targeted lanes** updated for any flag you touched (phase2-features workflow).
- [ ] **Meta**: `tests/meta/test_meta_files.py` passes; new flags added to `KNOWN_FEATURE_FLAGS`.
- [ ] **Observability**: If you added/changed metrics, they appear at `/metrics` when `NOVA_ENABLE_PROMETHEUS=1`.
- [ ] **Docs**: If you added flags/metrics, reflect in this framework + `ops/` assets (dashboards/alerts/runbooks).
- [ ] **Reversibility**: Change is flag-gated and can be disabled with zero behavioral drift.

## 12) Sunlight acceptance tests (must remain true)

1. **Provenance preserved**
   - Attestations include canonical body + `hash_method`; hash chain `prev` is correct.
2. **Immutability invariant**
   - Same canonical body → same digest; changes produce new events (append-only).
3. **Observability present**
   - `/metrics` gated correctly (404 when off; Prometheus content when on).
4. **Reversibility**
   - Toggling a flag reverts behavior without code edits and without breaking tests.
5. **Uncertainty transparent**
   - Claims carry assumptions/confidence; tests don't hide uncertainty with brittle expectations.

## 13) Documentation Integrity Protocol

**Purpose:** Prevent documentation drift and maintain architectural coherence through structured lifecycle management.

### Core Components

**📋 Canonical Documentation Index** (`docs/architecture/ontology/_canon.yaml`)
- Single source of truth for all documentation metadata
- Tracks lifecycle status, ontology versions, linked contracts/slots
- Enables programmatic reasoning about documentation state

**🔍 Automated Sunlight Scanner** (`scripts/maintenance/sunlight_scan.py`)
- Scans repository for documentation integrity violations
- Detects missing lifecycle tags, outdated references, orphaned files
- Run with: `python3 scripts/maintenance/sunlight_scan.py`

**📝 Future Work Ledger** (`docs/future/future_work_ledger.yaml`)
- Structured tracking of future enhancements and features
- Prevents idea drift by maintaining clear status tracking
- Status levels: CANDIDATE → PROPOSED → PLANNED → DEFERRED → CANCELLED

### Lifecycle Status Tags

Every documentation file must include lifecycle metadata:

```yaml
status: ACTIVE
superseded_by: null
linked_contracts:
  - orp@1.1.0
  - avl@1.1.0
ontology_version: 1.7.1
```

**Status Definitions:**
- `ACTIVE`: Currently authoritative and maintained
- `DEPRECATED`: Still valid but superseded (must specify `superseded_by`)
- `SUPERSEDED`: Replaced by newer documentation
- `CANDIDATE`: Proposed but not yet approved
- `FROZEN`: Historical reference, no longer updated
- `ARCHIVED`: Moved to archive, not for active use

### Documentation Rules

1. **Every document must declare lifecycle status**
2. **ACTIVE documents cannot contradict Mother Ontology**
3. **Contract-linked documents must list linked_contracts**
4. **Slot-specific documents must list linked_slots**
5. **Deprecated documents must have superseded_by field**
6. **Future work items go in future_work_ledger.yaml, not main docs**

### Pre-Merge Documentation Checklist

- [ ] **Lifecycle**: All modified/added docs have valid lifecycle tags
- [ ] **Canon**: New docs added to `docs/architecture/ontology/_canon.yaml`
- [ ] **Sunlight**: `scripts/maintenance/sunlight_scan.py` passes
- [ ] **Future Work**: Ideas tracked in `docs/future/future_work_ledger.yaml`
- [ ] **Ontology**: ACTIVE docs reference current ontology version (1.7.1)

### Automated Enforcement

**CI Lane** (`.github/workflows/docs.yaml`):
```yaml
- name: Documentation Integrity
  run: python3 scripts/maintenance/sunlight_scan.py
- name: Lifecycle Validation
  run: python3 scripts/maintenance/validate_lifecycle.py
```

**Auto-Archiving**: Files detected as outdated by sunlight scanner are automatically moved to `archive/` with proper metadata preservation.

**See also**
- Canonical Index: `docs/architecture/ontology/_canon.yaml`
- Future Work: `docs/future/future_work_ledger.yaml`
- Sunlight Scanner: `scripts/maintenance/sunlight_scan.py`
- Dashboards: `ops/dashboards/nova-phase2-observability.json`
- Alerts: `ops/alerts/nova-phase2.rules.yml`
- Runbooks: `ops/runbooks/`

