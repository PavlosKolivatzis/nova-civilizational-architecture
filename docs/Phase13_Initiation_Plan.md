# Phase 13: Autonomous Verification Ledger (AVL) — Initiation Plan

**Status:** Planning
**Phase:** 13
**Prerequisites:** Phase 12 complete (ORP physics validated, dual-modality agreement 100%)
**Purpose:** Establish immutable, self-auditing ledger of regime transitions and continuity proofs

---

## Context: Why Phase 13 Now?

Phase 12 validated that:
- ✅ Temporal semantics are correct (timestamps monotonic, durations accurate)
- ✅ ORP public API is stable (regime classification deterministic)
- ✅ Simulator is hardened (20 trajectories, 19 tests passing)
- ✅ Continuity logic is deterministic (ledger continuity preserved)
- ✅ Invariants are reliable (100% dual-modality agreement)

**The physics are correct. Now we need provenance.**

Phase 13 becomes meaningful only when every snapshot has:
- Consistent timestamps (✅ validated in Phase 12)
- Reproducible ORP evaluations (✅ dual-modality oracle confirms)
- Predictable amplitude/regime boundaries (✅ contract-verified)
- Dual-modality truth for real data (✅ simulator proves feasibility)

**Phase 13 enables:** Autonomous verification of live system behavior against contract expectations.

---

## Phase 13 Objectives

### 1. Autonomous Verification Ledger (AVL)
**Purpose:** Immutable append-only ledger of regime transitions with cryptographic integrity.

**Core Capabilities:**
- Record every regime transition with full provenance
- Capture contributing factors + dual-modality regime agreement
- Generate cryptographic hash chain (tamper-evident)
- Detect drift between ORP implementation and contract oracle
- Enable post-hoc audit of any time window

### 2. Drift Guards
**Purpose:** Real-time detection of ORP implementation divergence from contract.

**Triggers:**
- Dual-modality disagreement (ORP ≠ oracle)
- Invariant violation (hysteresis broken, min-duration ignored)
- Amplitude bounds exceeded
- Ledger continuity broken

**Response:**
- Log drift event with full context
- Optional: Halt transitions until manual review
- Alert operator via metrics/logs

### 3. Continuity Proofs
**Purpose:** Mathematical proofs that regime transitions preserve system continuity.

**Proofs:**
- Ledger continuity: from_regime[N] == to_regime[N-1]
- Temporal continuity: timestamps monotonic
- Amplitude continuity: no discontinuous jumps in threshold_multiplier/traffic_limit
- Regime continuity: transitions respect hysteresis + min-duration

---

## Deliverables

### 1. ADR-13-Init.md (Architecture Decision Record)
**File:** `docs/adr/ADR-13-Init.md`

**Sections:**
- Ledger design (schema, storage format, indexing)
- Invariants (what properties must hold across all entries)
- Contracts (AVL interface, query API, drift detection API)
- Drift guards (detection rules, response strategies)
- Migration path (simulation ledger → production AVL)

### 2. Autonomous Verification Ledger Implementation
**Files:**
- `src/nova/continuity/avl_ledger.py` - Core ledger logic
- `src/nova/continuity/drift_guard.py` - Drift detection engine
- `src/nova/continuity/continuity_proof.py` - Proof validators

**Schema:**
```python
@dataclass
class AVLEntry:
    """Autonomous Verification Ledger entry."""
    entry_id: str  # SHA256 of (timestamp + regime + factors)
    prev_entry_hash: str  # Hash chain pointer
    timestamp: str  # ISO8601 with timezone

    # ORP evaluation
    orp_regime: str
    orp_regime_score: float
    contributing_factors: Dict[str, float]
    posture_adjustments: Dict[str, Any]

    # Oracle verification
    oracle_regime: str
    oracle_regime_score: float
    dual_modality_agreement: bool

    # Transition metadata
    transition_from: Optional[str]
    time_in_previous_regime_s: float

    # Invariants
    hysteresis_enforced: bool
    min_duration_enforced: bool
    ledger_continuity: bool
    amplitude_valid: bool

    # Drift detection
    drift_detected: bool
    drift_reasons: List[str]
```

### 3. Checklists for Implementation
**File:** `docs/Phase13_Implementation_Checklist.md`

**Claude CLI Checklist:**
- [ ] Create AVL ledger module
- [ ] Implement hash chain logic
- [ ] Add drift detection rules
- [ ] Integrate with ORP evaluation
- [ ] Add AVL query API
- [ ] Write unit tests (ledger, drift, proofs)
- [ ] Write integration tests (ORP + AVL)
- [ ] Add Prometheus metrics (drift events, ledger size)

**Kilo Code Checklist:**
- [ ] Review ledger schema (immutability, indexing)
- [ ] Validate drift detection rules (false positive rate)
- [ ] Verify proof validators (mathematical correctness)
- [ ] Test hash chain integrity (tampering detection)
- [ ] Performance test (ledger write throughput)

### 4. CI Test Matrix for Phase 13
**File:** `.github/workflows/phase13-avl.yml`

**Test Lanes:**
```yaml
test-matrix:
  - avl-ledger-unit:
      - test_entry_creation
      - test_hash_chain_integrity
      - test_ledger_append_only
      - test_query_by_time_window
      - test_query_by_regime

  - drift-detection-unit:
      - test_dual_modality_drift
      - test_invariant_violation_drift
      - test_amplitude_bounds_drift
      - test_no_false_positives

  - continuity-proofs-unit:
      - test_ledger_continuity_proof
      - test_temporal_continuity_proof
      - test_amplitude_continuity_proof
      - test_regime_continuity_proof

  - avl-integration:
      - test_orp_to_avl_flow
      - test_drift_guard_halts_on_violation
      - test_ledger_survives_restart
      - test_query_api_accuracy

  - avl-e2e:
      - test_20_trajectories_to_avl
      - test_no_drift_across_trajectories
      - test_continuity_proofs_hold
```

### 5. Migration Mapping
**File:** `docs/Phase13_Migration_Map.md`

**Simulation → Ledger Entry Mapping:**

| Simulation Output | AVL Entry Field | Transformation |
|-------------------|-----------------|----------------|
| `step_result.timestamp` | `timestamp` | Direct copy (already ISO8601) |
| `step_result.orp_regime` | `orp_regime` | Direct copy |
| `step_result.orp_regime_score` | `orp_regime_score` | Direct copy |
| `step_result.contributing_factors` | `contributing_factors` | Direct copy |
| `step_result.oracle_regime` | `oracle_regime` | Direct copy |
| `step_result.dual_modality_agreement` | `dual_modality_agreement` | Direct copy |
| `step_result.violations` | `drift_reasons` | Map violations → drift_detected=True |
| Previous entry hash | `prev_entry_hash` | Compute SHA256(prev_entry) |
| `(timestamp, regime, factors)` | `entry_id` | Compute SHA256(concat) |

**Ledger Storage:**
- Format: JSON Lines (`.jsonl`) - one entry per line
- Location: `data/avl/avl_ledger.jsonl` (default)
- Rotation: None (append-only, infinite growth)
- Indexing: In-memory index by timestamp + regime (rebuild on load)

---

## Phase 13 Acceptance Criteria

### Ledger Integrity ✅
- [ ] All entries have valid hash chain (prev_entry_hash matches)
- [ ] Entry IDs are unique and deterministic
- [ ] Ledger is append-only (no modifications detected)
- [ ] Ledger survives process restart (persistence verified)

### Drift Detection ✅
- [ ] Dual-modality drift detected in <100ms
- [ ] No false positives across 20 canonical trajectories
- [ ] Drift events logged with full context (factors, scores, timestamp)
- [ ] Optional halt-on-drift configurable

### Continuity Proofs ✅
- [ ] Ledger continuity proven for 100% of transitions
- [ ] Temporal continuity proven (timestamps monotonic)
- [ ] Amplitude continuity proven (no discontinuous jumps)
- [ ] Regime continuity proven (hysteresis + min-duration respected)

### Query API ✅
- [ ] Query by time window returns correct entries
- [ ] Query by regime returns all matching entries
- [ ] Query by drift_detected returns only drift events
- [ ] Query performance <10ms for 1000-entry ledger

### Integration ✅
- [ ] ORP evaluation automatically writes to AVL
- [ ] Drift guard triggers on first invariant violation
- [ ] Ledger integrates with Prometheus (metrics exported)
- [ ] AVL survives ORP engine restart (ledger persisted)

---

## Implementation Plan (6 Steps)

### Step 1: AVL Ledger Core (Day 1)
**Deliverables:**
- `src/nova/continuity/avl_ledger.py`
- Entry schema (dataclass)
- Hash chain logic
- Append/query API
- Unit tests (15 tests)

**Acceptance:** Ledger can append entries, compute hashes, query by timestamp.

### Step 2: Drift Guard (Day 1-2)
**Deliverables:**
- `src/nova/continuity/drift_guard.py`
- Drift detection rules (4 categories)
- Drift event logging
- Unit tests (10 tests)

**Acceptance:** Detects dual-modality drift, invariant violations, amplitude bounds violations.

### Step 3: Continuity Proofs (Day 2)
**Deliverables:**
- `src/nova/continuity/continuity_proof.py`
- Ledger continuity validator
- Temporal continuity validator
- Amplitude continuity validator
- Regime continuity validator
- Unit tests (8 tests)

**Acceptance:** All proofs hold across 20 canonical trajectories.

### Step 4: ORP Integration (Day 2-3)
**Deliverables:**
- Update `src/nova/continuity/operational_regime.py`
- Add AVL write after each ORP evaluation
- Add drift guard check before transition
- Integration tests (5 tests)

**Acceptance:** ORP evaluations automatically write to AVL, drift guard triggers on violations.

### Step 5: E2E Validation (Day 3)
**Deliverables:**
- Run all 20 trajectories through ORP + AVL
- Validate ledger integrity (hash chain)
- Validate no drift detected on canonical trajectories
- Validate continuity proofs hold

**Acceptance:** All 20 trajectories → ledger with zero drift, all proofs hold.

### Step 6: Documentation + ADR (Day 3-4)
**Deliverables:**
- `docs/adr/ADR-13-Init.md`
- `docs/Phase13_Implementation_Checklist.md`
- `docs/Phase13_Migration_Map.md`
- Update Phase 13 plan with final results

**Acceptance:** Documentation complete, ready for production deployment.

---

## Rollback Plan

If Phase 13 reveals issues:
1. **Drift detection too sensitive:** Tune thresholds, add tolerance parameter
2. **Ledger growth too fast:** Add rotation/archival strategy
3. **Hash chain breaks:** Debug hash computation, fix determinism
4. **Query performance poor:** Add indexing (timestamp, regime)
5. **ORP integration unstable:** Add flag `NOVA_ENABLE_AVL=0` to disable

**No changes to ORP physics** - Phase 13 is pure observation/verification layer.

---

## Dependencies

**Phase 12 artifacts required:**
- `src/nova/continuity/contract_oracle.py` - Dual-modality verification
- `scripts/simulate_nova_cycle.py` - Simulation engine (pattern for AVL)
- `tests/e2e/trajectories/*.json` - Test data

**New dependencies:**
- None (uses stdlib `hashlib` for SHA256)

---

## Success Metrics

**Quantitative:**
- Ledger entries: 300+ (across 20 trajectories)
- Drift events: 0 (on canonical trajectories)
- Hash chain breaks: 0
- Query latency: <10ms (1000 entries)
- Continuity proofs: 100% passing

**Qualitative:**
- Ledger is human-readable (JSON Lines)
- Drift events are actionable (full context logged)
- Proofs are mathematical (not heuristic)
- Integration is transparent (no ORP behavior change)

---

## Next Steps

1. **Create ADR-13-Init.md** with detailed design decisions
2. **Implement AVL ledger core** (Step 1)
3. **Add drift detection** (Step 2)
4. **Validate with trajectories** (Step 5)
5. **Document + commit**

**Estimated duration:** 3-4 days (Steps 1-6)

**Ready to begin:** Phase 12 foundation validated, all prerequisites met.
