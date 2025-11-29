# Phase 13: Implementation Checklist

**Phase:** 13 - Autonomous Verification Ledger (AVL)
**Status:** Planning → Implementation
**Reference:** `docs/Phase13_Initiation_Plan.md`, `docs/adr/ADR-13-Init.md`

---

## Claude CLI Checklist

### Step 1: AVL Ledger Core (Day 1)

- [ ] **Create `src/nova/continuity/avl_ledger.py`**
  - [ ] Define `AVLEntry` dataclass with all fields from ADR-13
  - [ ] Implement `compute_entry_hash()` with canonical JSON ordering
  - [ ] Implement `AVLLedger` class with `__init__`, `append()`, `query_*()` methods
  - [ ] Add atomic file writes (temp file + rename pattern)
  - [ ] Add ledger persistence (load from file on init)

- [ ] **Write unit tests: `tests/continuity/test_avl_ledger.py`**
  - [ ] `test_entry_creation` - Validate AVLEntry dataclass
  - [ ] `test_compute_entry_hash_deterministic` - Same inputs → same hash
  - [ ] `test_hash_chain_integrity` - Genesis + chain validation
  - [ ] `test_ledger_append_only` - No modifications allowed
  - [ ] `test_ledger_persistence` - Survives restart
  - [ ] `test_query_by_time_window` - Time range queries work
  - [ ] `test_query_by_regime` - Regime filtering works
  - [ ] `test_query_drift_events` - Drift filtering works
  - [ ] `test_get_latest` - Last N entries retrieval
  - [ ] `test_verify_integrity` - Hash chain + proofs
  - [ ] `test_ledger_empty_state` - Genesis entry handling
  - [ ] `test_ledger_concurrent_append` - Thread safety (future)
  - [ ] `test_export_jsonl` - Export to file
  - [ ] `test_import_jsonl` - Import from file
  - [ ] `test_entry_id_unique` - No duplicate IDs

**Acceptance:** 15 tests passing, ledger can append + query + verify.

---

### Step 2: Drift Guard (Day 1-2)

- [ ] **Create `src/nova/continuity/drift_guard.py`**
  - [ ] Define `DriftGuard` class
  - [ ] Implement `check()` method with 4 drift detection rules:
    - [ ] Dual-modality disagreement (ORP ≠ oracle)
    - [ ] Invariant violation (hysteresis, min-duration, ledger continuity, amplitude)
    - [ ] Amplitude bounds exceeded
    - [ ] Score computation drift (|ORP_score - oracle_score| > 1e-6)
  - [ ] Implement `configure()` for halt-on-drift setting
  - [ ] Add drift reason generation (human-readable messages)

- [ ] **Write unit tests: `tests/continuity/test_drift_guard.py`**
  - [ ] `test_dual_modality_drift_detected` - ORP ≠ oracle triggers drift
  - [ ] `test_invariant_violation_drift` - Failed invariant triggers drift
  - [ ] `test_amplitude_bounds_drift` - Out-of-bounds triggers drift
  - [ ] `test_score_drift_detected` - Score mismatch triggers drift
  - [ ] `test_no_drift_on_valid_entry` - No false positives
  - [ ] `test_drift_reasons_accurate` - Reason messages correct
  - [ ] `test_halt_on_drift_configurable` - Halt setting works
  - [ ] `test_multiple_drift_reasons` - Multiple violations reported
  - [ ] `test_drift_threshold_tunable` - Score drift threshold adjustable
  - [ ] `test_drift_guard_disabled` - Can disable drift detection

**Acceptance:** 10 tests passing, drift detection working with zero false positives on canonical data.

---

### Step 3: Continuity Proofs (Day 2)

- [ ] **Create `src/nova/continuity/continuity_proof.py`**
  - [ ] Define `ContinuityProof` class
  - [ ] Implement `prove_ledger_continuity()` - from_regime[N] == to_regime[N-1]
  - [ ] Implement `prove_temporal_continuity()` - Timestamps monotonic
  - [ ] Implement `prove_amplitude_continuity()` - No discontinuous jumps
  - [ ] Implement `prove_regime_continuity()` - Hysteresis + min-duration respected
  - [ ] Implement `prove_all()` - Run all proofs, return dict

- [ ] **Write unit tests: `tests/continuity/test_continuity_proof.py`**
  - [ ] `test_ledger_continuity_proof_pass` - Valid ledger passes
  - [ ] `test_ledger_continuity_proof_fail` - Broken continuity detected
  - [ ] `test_temporal_continuity_proof_pass` - Monotonic timestamps pass
  - [ ] `test_temporal_continuity_proof_fail` - Out-of-order detected
  - [ ] `test_amplitude_continuity_proof_pass` - Smooth transitions pass
  - [ ] `test_amplitude_continuity_proof_fail` - Discontinuity detected
  - [ ] `test_regime_continuity_proof_pass` - Invariants respected
  - [ ] `test_regime_continuity_proof_fail` - Invariant violation detected

**Acceptance:** 8 tests passing, all proofs validate correctly.

---

### Step 4: ORP Integration (Day 2-3)

- [ ] **Update `src/nova/continuity/operational_regime.py`**
  - [ ] Add `_avl_enabled()` flag check (`NOVA_ENABLE_AVL`)
  - [ ] Add `_snapshot_to_avl_entry()` conversion function
  - [ ] Update `evaluate()` to write to AVL after regime evaluation
  - [ ] Add drift guard check before returning snapshot
  - [ ] Add exception handling for AVL write failures (log, don't crash)
  - [ ] Add Prometheus metrics:
    - [ ] `nova_avl_entries_total` - Counter of ledger entries
    - [ ] `nova_avl_drift_events_total` - Counter of drift detections
    - [ ] `nova_avl_write_errors_total` - Counter of write failures

- [ ] **Write integration tests: `tests/integration/test_orp_avl.py`**
  - [ ] `test_orp_evaluation_writes_to_avl` - AVL entry created on evaluate()
  - [ ] `test_drift_guard_triggers_on_violation` - Drift detection works in live flow
  - [ ] `test_avl_disabled_by_default` - No AVL writes when disabled
  - [ ] `test_avl_survives_orp_restart` - Ledger persists across restarts
  - [ ] `test_prometheus_metrics_incremented` - Metrics updated correctly

**Acceptance:** 5 integration tests passing, ORP + AVL flow working.

---

### Step 5: E2E Validation (Day 3)

- [ ] **Run all 20 trajectories through ORP + AVL**
  - [ ] Modify `scripts/simulate_nova_cycle.py` to enable AVL
  - [ ] Run each trajectory, verify ledger written
  - [ ] Verify hash chain integrity on all ledgers
  - [ ] Verify zero drift detected on canonical trajectories
  - [ ] Verify all continuity proofs pass

- [ ] **Create validation script: `scripts/validate_avl_e2e.py`**
  - [ ] Load all 20 trajectory ledgers
  - [ ] Run `verify_integrity()` on each
  - [ ] Run `prove_all()` on each
  - [ ] Collect summary (total entries, drift events, proof results)
  - [ ] Output pass/fail report

**Acceptance:** All 20 trajectories → ledger with zero drift, all proofs hold.

---

### Step 6: Documentation + ADR (Day 3-4)

- [x] **Create `docs/adr/ADR-13-Init.md`** ✅ Done
- [x] **Create `docs/Phase13_Implementation_Checklist.md`** ✅ Done (this file)
- [ ] **Create `docs/Phase13_Migration_Map.md`**
- [ ] **Update `docs/Phase13_Initiation_Plan.md` with final results**
- [ ] **Add Prometheus metrics documentation**
- [ ] **Add AVL query API examples**
- [ ] **Update README with Phase 13 summary**

**Acceptance:** Documentation complete, ready for production deployment.

---

## Kilo Code Review Checklist

### Ledger Design Review
- [ ] **Schema completeness** - All necessary fields present?
- [ ] **Hash algorithm** - SHA256 appropriate? Collision risk acceptable?
- [ ] **Storage format** - JSON Lines vs alternatives (Parquet, SQLite)?
- [ ] **Indexing strategy** - Linear scan acceptable for v1? When to add indexes?
- [ ] **Rotation policy** - Unbounded growth acceptable? Archival strategy?

### Drift Detection Review
- [ ] **False positive rate** - Acceptable on real data?
- [ ] **Threshold tuning** - Score drift 1e-6 appropriate?
- [ ] **Halt-on-drift safety** - Safe to halt transitions? Recovery path?
- [ ] **Drift suppression** - Need rate limiting (e.g., max 1 alert/minute)?

### Continuity Proofs Review
- [ ] **Mathematical correctness** - Proofs sound?
- [ ] **Edge cases** - Empty ledger, single entry, genesis entry?
- [ ] **Amplitude delta** - 0.5 threshold appropriate for continuity?
- [ ] **Proof composition** - Can combine proofs into single verification?

### Performance Review
- [ ] **Hash computation cost** - <1ms acceptable?
- [ ] **File I/O blocking** - Async writes needed?
- [ ] **Query performance** - Linear scan acceptable for <10k entries?
- [ ] **Memory footprint** - In-memory ledger scalable?

### Security Review
- [ ] **Tampering detection** - Hash chain sufficient?
- [ ] **Access control** - Ledger file permissions?
- [ ] **Entry injection** - Can adversary forge entries?
- [ ] **Hash chain bypass** - Can adversary break chain without detection?

---

## CI Test Matrix

See `.github/workflows/phase13-avl.yml` for full test configuration.

**Test lanes:**
- `avl-ledger-unit` - 15 tests
- `drift-detection-unit` - 10 tests
- `continuity-proofs-unit` - 8 tests
- `avl-integration` - 5 tests
- `avl-e2e` - 20 trajectories × validation

**Total:** 38 new tests + 20 E2E validations

---

## Progress Tracking

**Current status:** Planning complete, ready to begin Step 1.

### Completed:
- [x] Phase 13 Initiation Plan
- [x] ADR-13-Init design document
- [x] Implementation checklist (this file)

### In Progress:
- [ ] Step 1: AVL Ledger Core

### Blocked:
- None

---

## Rollback Markers

If issues arise, revert to these commits:
- **Phase 12 baseline:** `2de9b96` (timestamp fix)
- **Pre-Phase 13:** `<commit before AVL>`

**Rollback command:**
```bash
# Disable AVL
export NOVA_ENABLE_AVL=0

# Or revert code
git revert <avl-commit-range>
```

---

## Notes

- AVL is **observation-only** - no changes to ORP physics
- All tests must pass before Step N+1
- Drift detection tuning may require iteration
- Performance profiling needed if ledger >10k entries
- Consider async writes in Step 7 (future optimization)
