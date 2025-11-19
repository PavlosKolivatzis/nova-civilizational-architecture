# Slot01 Root-Mode Migration Plan (Option B)

**Status**: In Progress
**Flag**: `NOVA_SLOT01_ROOT_MODE=1`
**Doctrine**: Slot04 canonizes truth → Slot01 attests truth

---

## Alignment With Nova Doctrine

From `agents/nova_ai_operating_framework.md`:
> **"Honor the separation: slots interpret, core attests"**

**Before**: Slot01 violated separation (interpreted AND attested)
**After**: Slot01 = attest layer, Slot04 TRI = interpret layer

**Canonical Flow**:
```
Slots 2/3/5 → Observe
    ↓
Slot04 TRI → Canonize (tri_coherence, drift_z, phase_jitter)
    ↓
Slot01 → Attest (register anchor_id ← TRI hash)
    ↓
Ledgers → Publish (append-only, hash-linked)
```

---

## Phase 1: Migration Flag (Reversible Rollout)

**Flag**: `NOVA_SLOT01_ROOT_MODE`
**Default**: `0` (preserve old behavior)
**When enabled**: `1` (Root-Mode adapter active)

**Implementation**:
- Add flag to `KNOWN_FEATURE_FLAGS` in `tests/meta/test_meta_files.py`
- Add conditional in `src/nova/slots/slot01_truth_anchor/orchestrator_adapter.py`
- Preserve old adapter logic behind flag check
- Add Prometheus metric: `nova_feature_flag_enabled{flag="NOVA_SLOT01_ROOT_MODE"}`

**Rollback**: Set `NOVA_SLOT01_ROOT_MODE=0` to restore inference behavior

---

## Phase 2: TRI Signal Mapping (Truth Canonization)

**Old Slot01 Signals** → **New TRI Signals**:

| Old Signal (Slot01) | New Signal (Slot04 TRI) | Semantic Mirror Key | Usage |
|---------------------|-------------------------|---------------------|-------|
| `truth_score` | `tri_coherence` | `slot04.tri_coherence` | Epistemic confidence |
| `critical` | `tri_drift_z > threshold` | `slot04.tri_drift_z` | Stability alarm |
| `anchor_stable` | `phase_jitter < epsilon` | `slot04.phase_jitter` | Phase lock stability |

**Evidence**: TRI signals already published to Semantic Mirror (`orchestrator/app.py:138-145`)

**No new code required** — reroute downstream consumers.

---

## Phase 3: Downstream Slot Refactoring

### Slot03 Emotional Matrix

**Current dependencies**:
- `truth_score` from Slot01 (inference)
- `critical` flag for escalation

**New dependencies**:
```python
# OLD (violates separation)
truth_score = slot01_result.data["truth_score"]
critical = slot01_result.data["critical"]

# NEW (doctrine-aligned)
from orchestrator.semantic_mirror import get_semantic_mirror
sm = get_semantic_mirror()
tri_coherence = sm.get_context("slot04.tri_coherence", "slot03")
tri_drift_z = sm.get_context("slot04.tri_drift_z", "slot03")

escalate = (tri_coherence < 0.5) or (tri_drift_z > 2.0)
```

**Files to modify**:
- `src/nova/slots/slot03_emotional_matrix/*.py` (adapter + core logic)
- `tests/test_slot03_emotional_matrix.py` (inject TRI fixtures)

---

### Slot06 Cultural Synthesis

**Current dependencies**:
- `anchor_stable` for cultural calibration

**New dependencies**:
```python
# OLD
anchor_stable = slot01_result.data["anchor_stable"]

# NEW
tri_coherence = sm.get_context("slot04.tri_coherence", "slot06")
phase_jitter = sm.get_context("slot04.phase_jitter", "slot06")
cultural_stability = (tri_coherence > 0.7) and (phase_jitter < 0.1)
```

**Files to modify**:
- `src/nova/slots/slot06_cultural_synthesis/*.py`
- `tests/test_slot06_cultural_synthesis.py`

---

### Slot07 Production Controls

**Current dependencies**:
- `truth_score` for backpressure heuristics

**New dependencies**:
```python
# Already implemented in orchestrator/app.py:149-157
system_pressure_level = sm.get_context("slot07.pressure_level", "anomaly_detector")
tri_drift_z = sm.get_context("slot04.tri_drift_z", "slot07")

# Formalize breaker logic
breaker_threshold = tri_drift_z > float(os.getenv("SLOT07_TRI_DRIFT_THRESHOLD", "2.5"))
```

**Files to modify**:
- `src/nova/slots/slot07_production_controls/*.py` (document existing behavior)
- Add explicit TRI consumption contract

---

## Phase 4: TRI → Slot01 Attestation Flow

**New canonical operation**: Slot04 TRI outputs are attested as immutable anchors.

**Implementation**:
```python
# In Slot04 TRI adapter (after computing coherence)
from orchestrator.semantic_mirror import get_semantic_mirror
from src.nova.slots.slot01_truth_anchor import slot1_adapter
import hashlib

tri_report = {
    "coherence": tri_coherence,
    "drift_z": tri_drift_z,
    "phase_jitter": phase_jitter,
    "timestamp": time.time(),
    "request_id": request_id,
}

# Canonicalize for hashing
tri_canonical = json.dumps(tri_report, sort_keys=True)
tri_hash = hashlib.sha256(tri_canonical.encode()).hexdigest()

# Attest to Slot01
await slot1_adapter.run({
    "op": "register",
    "anchor_id": f"tri.{request_id}.{tri_hash[:16]}",
    "value": tri_canonical,
    "metadata": {
        "source": "slot04_tri",
        "tri_coherence": tri_coherence,
        "tri_drift_z": tri_drift_z,
        "phase_jitter": phase_jitter,
        "provenance_hash": tri_hash,
    }
}, request_id=request_id)
```

**Files to create**:
- `src/nova/slots/slot04_tri/attestation.py` (TRI → Anchor bridge)
- `tests/integration/test_tri_to_anchor_attestation.py`

---

## Phase 5: Observability Layer

**New Prometheus Metrics**:
```python
from prometheus_client import Counter, Histogram

tri_to_anchor_attest_total = Counter(
    "nova_tri_to_anchor_attest_total",
    "Total TRI reports attested to Slot01",
    ["status"]
)

tri_anchor_write_latency_ms = Histogram(
    "nova_tri_anchor_write_latency_ms",
    "Latency of TRI → Anchor attestation writes",
    buckets=[10, 50, 100, 250, 500, 1000]
)

tri_canonized_total = Counter(
    "nova_tri_canonized_total",
    "Total TRI canonization operations",
    ["result"]
)

slot01_attest_provenance_mismatch_total = Counter(
    "nova_slot01_attest_provenance_mismatch_total",
    "Attestation provenance hash mismatches"
)
```

**New Observability Endpoint**:
```python
@app.get("/observability/tri_to_anchor")
async def tri_to_anchor_observability():
    """Export TRI → Anchor attestation status."""
    from orchestrator.tri_anchor_bridge import get_last_attestation
    last = get_last_attestation()
    return {
        "last_triangulated_anchor_id": last.get("anchor_id"),
        "last_tri_coherence": last.get("tri_coherence"),
        "last_tri_drift_z": last.get("drift_z"),
        "last_phase_jitter": last.get("phase_jitter"),
        "timestamp": last.get("timestamp"),
        "provenance_hash": last.get("provenance_hash"),
    }
```

**Files to modify**:
- `orchestrator/prometheus_metrics.py` (add metrics)
- `orchestrator/app.py` (add endpoint)

---

## Phase 6: Contract Updates

**Files to modify**:
```yaml
# contracts/slot03_emotional_matrix@1.yaml
inputs:
  - tri_coherence  # NEW (was: truth_score)
  - tri_drift_z    # NEW (was: critical)

# contracts/slot06_cultural_synthesis@1.yaml
inputs:
  - tri_coherence
  - phase_jitter   # NEW (was: anchor_stable)

# contracts/slot07_production_controls@1.yaml
inputs:
  - tri_drift_z    # Formalize existing usage
```

**New contract**:
```yaml
# contracts/tri_to_anchor_attest@1.yaml
schema_version: "1.0"
id: TRI_TO_ANCHOR_ATTEST
version: 1
description: "Slot04 TRI canonization attested to Slot01 immutable anchor"

producer: slot04_tri
consumer: slot01_truth_anchor

payload:
  tri_report:
    type: object
    fields:
      - name: coherence
        type: float
      - name: drift_z
        type: float
      - name: phase_jitter
        type: float
      - name: timestamp
        type: float
      - name: provenance_hash
        type: string
        description: "SHA-256 of canonicalized TRI report"

attestation:
  anchor_id_format: "tri.{request_id}.{hash[:16]}"
  immutable: true
  ledger_write: true
```

---

## Phase 7: Test Suite Transformation

**Remove old Slot01 inference tests**:
- ❌ `test_run_success_returns_slotresult_ok` (expects SlotResult)
- ❌ `test_run_rejects_invalid_payload_type` (expects content payload)
- ❌ `test_analyze_content_*` (inference removed)

**Add Root-Mode tests**:
```python
# tests/test_slot01_root_mode.py
import pytest
from src.nova.slots.slot01_truth_anchor import slot1_adapter

@pytest.mark.asyncio
async def test_root_mode_register():
    result = await slot1_adapter.run({
        "op": "register",
        "anchor_id": "test.anchor.001",
        "value": "immutable_truth",
        "metadata": {"source": "test"}
    }, request_id="req-001")

    assert result["success"] is True
    assert result["status"] == "ok"

@pytest.mark.asyncio
async def test_root_mode_lookup():
    await slot1_adapter.run({
        "op": "register",
        "anchor_id": "test.anchor.002",
        "value": "test_value"
    }, request_id="req-002")

    result = await slot1_adapter.run({
        "op": "lookup",
        "anchor_id": "test.anchor.002"
    }, request_id="req-003")

    assert result["success"] is True
    assert result["found"] is True
    assert result["value"] == "test_value"

@pytest.mark.asyncio
async def test_root_mode_verify():
    await slot1_adapter.run({
        "op": "register",
        "anchor_id": "test.anchor.003",
        "value": "verify_me"
    }, request_id="req-004")

    result = await slot1_adapter.run({
        "op": "verify",
        "anchor_id": "test.anchor.003",
        "claim": "verify_me"
    }, request_id="req-005")

    assert result["success"] is True
    assert result["valid"] is True
```

**Add TRI integration tests**:
```python
# tests/integration/test_tri_to_anchor_flow.py
@pytest.mark.integration
async def test_tri_canonization_attests_to_slot01():
    """Test Slot04 TRI → Slot01 anchor attestation flow."""
    # Compute TRI coherence
    tri_result = await slot4_tri_adapter.run({...})

    # Verify anchor created
    anchor_lookup = await slot1_adapter.run({
        "op": "lookup",
        "anchor_id": f"tri.{request_id}.*"
    })

    assert anchor_lookup["found"] is True
    assert anchor_lookup["metadata"]["tri_coherence"] == tri_result["coherence"]
```

---

## Phase 8: Final Consistency Sweep

**Documentation updates**:
- `docs/slots/slot01_truth_anchor.md` → Mark as "Attestation Layer (Root-Mode)"
- `docs/slots/slot04_tri.md` → Mark as "Truth Canonization Engine"
- `docs/ARCHITECTURE.md` → Update epistemic flow diagram
- `README.md` → Add `NOVA_SLOT01_ROOT_MODE` flag

**Ontology updates**:
- `specs/nova_framework_ontology.v1.yaml` → Already updated (Phase 0)

**Slot Map cleanup**:
- `contracts/slot_map.json` → Remove Slot01 inference capabilities

**Phase 14+ docs**:
- Reflect new epistemic architecture in governance docs

---

## Migration Checklist

- [ ] **Phase 1**: Add `NOVA_SLOT01_ROOT_MODE` flag
- [ ] **Phase 2**: Document TRI signal mappings
- [ ] **Phase 3**: Refactor Slot03/06/07 to consume TRI
- [ ] **Phase 4**: Implement TRI → Slot01 attestation
- [ ] **Phase 5**: Add Prometheus metrics + `/observability/tri_to_anchor`
- [ ] **Phase 6**: Update inter-slot contracts
- [ ] **Phase 7**: Write Root-Mode + TRI integration tests
- [ ] **Phase 8**: Documentation sweep

---

## Rollback Plan

**If migration fails**:
1. Set `NOVA_SLOT01_ROOT_MODE=0`
2. Old adapter behavior restored
3. Downstream slots revert to Slot01 signals
4. No code changes required

**Monitoring**:
- Watch `nova_feature_flag_enabled{flag="NOVA_SLOT01_ROOT_MODE"}` gauge
- Watch `nova_tri_to_anchor_attest_total` counter
- Watch `slot01_attest_provenance_mismatch_total` for integrity violations

---

## Success Criteria

✅ Slot01 operates in pure Root-Mode (zero inference)
✅ Slot04 TRI signals flow to Slot03/06/07
✅ TRI reports attested as immutable anchors
✅ All tests pass with `NOVA_SLOT01_ROOT_MODE=1`
✅ Prometheus metrics expose TRI → Anchor flow
✅ `/observability/tri_to_anchor` endpoint operational
✅ Contracts updated, ontology aligned
✅ Doctrine honored: "Slots interpret, core attests"

---

**Next Step**: Implement Phase 1 (migration flag).
