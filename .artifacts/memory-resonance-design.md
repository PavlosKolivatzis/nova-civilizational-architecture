# Memory Resonance Design (Phase 7 RC)
**Status:** Design Phase
**Target:** Phase 7.0-RC completion

---

## Mission
Transform predictive intelligence from **reactive foresight** (5-tick projection) to **long-term memory coherence** (7-day stability tracking + integrity scoring).

---

## Problem Statement

**Current gaps:**
1. **No accountability**: Predictions made but never validated against outcomes
2. **No trust metric**: Can't measure reliability of predictive layer over time
3. **No resilience test**: Unknown if system auto-recovers from stress
4. **No memory**: TRSI computed but not tracked longitudinally (only 1000 samples, no time bounds)

**RC Requirements:**
- Memory stability ≥ 0.80 (7-day rolling window)
- RIS score ≥ 0.75 (composite integrity)
- Stress recovery ≥ 0.90 within 24h

---

## Architecture

### Component Hierarchy
```
MemoryResonanceWindow (7-day TRSI storage)
    ↓ feeds
ResonanceIntegrity (RIS computation)
    ↓ feeds
GovernanceEngine (integrity-aware gating)
```

### Data Flow
```
1. TemporalEngine computes temporal_snapshot@1
2. TemporalResonanceEngine computes TRSI from belief propagation
3. MemoryResonanceWindow samples TRSI hourly → 7-day rolling buffer
4. ResonanceIntegrity computes RIS = (TRSI × Ethics × Latency)^(1/3)
5. GovernanceEngine uses RIS for trust-weighted decisions
```

---

## Design Decisions

### 1. Sampling Strategy

**Options:**
- **A. Hourly sampling** (7 × 24 = 168 samples)
- B. 15-min sampling (7 × 24 × 4 = 672 samples)
- C. Per-request sampling (unbounded, memory risk)

**Choice: A (Hourly)**

**Rationale:**
- RC blueprint specifies `trsi_history = deque(maxlen=7*24)`
- 168 samples sufficient for trend detection
- Reduces storage/compute overhead
- Aligned with "hourly" cadence in blueprint

**Trade-off:** Misses sub-hour volatility spikes

---

### 2. Storage Backend

**Options:**
- **A. In-memory deque** (simple, stateless, volatile)
- B. Ledger-backed (persistent, auditable, heavy)
- C. Semantic mirror (TTL-based, distributed)

**Choice: A (In-memory deque)**

**Rationale:**
- RC is validation phase, not production
- 168 floats = ~1.3 KB memory (negligible)
- Stateless restart acceptable (7-day warm-up)
- Avoids ledger write overhead

**Migration path:** If promoted to production, move to ledger-backed storage

---

### 3. Memory Stability Formula

**Blueprint formula:**
```python
stability = max(0.0, min(1.0, mean_trsi - volatility))
```

**Analysis:**
- `mean_trsi`: Baseline temporal coherence (higher = better)
- `volatility`: Standard deviation (lower = more stable)
- `mean - stdev`: Penalizes high variance even if mean is good

**Critique:**
- **Weakness:** Can go negative if `stdev > mean` (clamped to 0)
- **Example:** mean=0.6, stdev=0.7 → stability=0.0 (harsh)

**Alternative formula:**
```python
# Coefficient of variation (CV) approach
stability = mean_trsi * (1 - min(1.0, stdev / mean_trsi))
```

**Comparison:**
| Scenario | mean | stdev | Blueprint | CV Approach |
|----------|------|-------|-----------|-------------|
| Stable high | 0.9 | 0.05 | 0.85 | 0.85 |
| Stable low | 0.5 | 0.05 | 0.45 | 0.45 |
| Volatile high | 0.8 | 0.3 | 0.50 | 0.70 |
| Volatile low | 0.5 | 0.4 | 0.10 | 0.10 |

**Decision: Use Blueprint formula**

**Rationale:**
- Specified in RC blueprint (consistency with design)
- More conservative (fails-closed on volatility)
- Simpler to reason about

**Risk mitigation:** Document threshold (≥0.80) assumes reasonably stable TRSI (stdev <0.2)

---

### 4. RIS (Resonance Integrity Score)

**Formula (blueprint):**
```python
RIS = (TRSI × Ethics × (1 - Latency_Penalty))^(1/3)
```

**Components:**

#### a) TRSI Component
- **Source:** Current `temporal_resonance.py::compute_trsi()`
- **Range:** [0.0, 1.0]
- **Interpretation:** Temporal coherence quality

#### b) Ethics Component
- **Source:** Governance ethics checks
- **Calculation:** `1 - (violation_count / total_checks)`
- **Range:** [0.0, 1.0]
- **Interpretation:** Derivative learning compliance

**Question:** Where to get ethics score?

**Options:**
- A. Aggregate from `GovernanceResult.ethics` (list of EthicsCheck)
- B. New ethics ledger query
- C. Hardcoded 1.0 (optimistic)

**Choice: A (Aggregate from GovernanceResult)**

```python
def compute_ethics_score(ethics_checks: list[EthicsCheck]) -> float:
    if not ethics_checks:
        return 1.0  # No checks = full compliance
    passed = sum(1 for check in ethics_checks if check.passed)
    return passed / len(ethics_checks)
```

#### c) Latency Penalty Component
- **Source:** Time delta between prediction and governance decision
- **Formula:** `penalty = min(1.0, max(0.0, (latency_hours - 2) / 22))`
  - 0 penalty for <2h
  - 1 penalty for >24h
  - Linear ramp between

**Question:** How to measure latency?

**Options:**
- A. Track `predictive_snapshot.timestamp` vs. `governance_result.timestamp`
- B. Track controller response time (from temporal engine)
- C. Skip (assume instant, penalty=0)

**Choice: C (Skip for RC, penalty=0)**

**Rationale:**
- Orchestrator runs synchronously (no async delay)
- Latency component designed for distributed systems
- RC validation doesn't require latency measurement

**Migration path:** Add latency tracking if federated deployment

#### d) Cubic Mean Justification

**Why cubic root, not arithmetic mean?**

```
Arithmetic: RIS = (TRSI + Ethics + Latency) / 3
Geometric:  RIS = (TRSI × Ethics × Latency)^(1/3)
```

**Geometric properties:**
- **Multiplicative penalty:** One component at 0 → RIS = 0 (fail-closed)
- **Balanced weighting:** All components equally important
- **Example:** TRSI=0.9, Ethics=0.9, Latency=0.9 → RIS=0.90 (not 0.90/3=0.30)

**Decision: Use geometric (cubic) mean per blueprint**

---

### 5. Integration Points

#### a) Where to compute memory stability?
- **Option A:** In `PredictiveTrajectoryEngine` (predictive layer)
- **Option B:** In `GovernanceEngine` (governance layer)
- **Option C:** New `MemoryResonanceService` (separate component)

**Choice: C (Separate component)**

**Rationale:**
- Memory resonance is **observability**, not **prediction** or **governance**
- Read-only observer (no side effects)
- Can run independently for analysis

#### b) Where to compute RIS?
- Same as memory stability (separate component)

#### c) Where to store 7-day window?
- In-memory in `MemoryResonanceService` instance
- Singleton pattern (one window per process)

#### d) How to trigger hourly sampling?
- **Option A:** Cron job / scheduler
- **Option B:** On-demand (sample when `compute()` called)
- **Option C:** Governance engine callback

**Choice: B (On-demand)**

**Rationale:**
- RC is validation, not production
- Hourly sampling happens naturally if governance runs hourly
- Avoids scheduler complexity

**Trade-off:** Sampling tied to governance frequency

---

### 6. Stress Simulation Design

**Goal:** Inject controlled TRSI drift, measure auto-recovery

**Approach:**
1. **Baseline measurement:** Capture current TRSI
2. **Drift injection:** Mock temporal snapshot with elevated drift_z
3. **Recovery monitoring:** Sample TRSI every tick for N ticks
4. **Recovery metrics:**
   - Time to 90% recovery (hours)
   - Max deviation from baseline
   - Recovery rate (linear regression slope)

**Question:** How to inject drift?

**Options:**
- A. Mock temporal ledger entries with high drift
- B. Override `_tri_signal_from_request()` with synthetic data
- C. Modify thresholds to artificially trigger gates

**Choice: A (Mock ledger entries)**

**Rationale:**
- Most realistic (exercises actual code paths)
- Deterministic (repeatable in CI)
- Safe (runs in isolated test)

**Implementation:**
```python
def inject_temporal_drift(ledger, magnitude=0.1, duration_ticks=10):
    """Inject synthetic drift into temporal ledger."""
    baseline_drift = ledger.get_latest_drift()
    for tick in range(duration_ticks):
        synthetic_snapshot = create_snapshot(
            tri_drift_z=baseline_drift + magnitude,
            timestamp=time.time() + tick
        )
        ledger.append(synthetic_snapshot)
```

---

## Implementation Plan

### Phase 1: Memory Window (1-2 hours)
- [ ] Create `orchestrator/predictive/memory_resonance.py`
- [ ] Implement `MemoryResonanceWindow` class
- [ ] Add `add_trsi_sample()` and `compute_memory_stability()`
- [ ] Unit tests for rolling window + stability calculation

### Phase 2: RIS Computation (1 hour)
- [ ] Create `orchestrator/predictive/resonance_integrity.py`
- [ ] Implement `compute_ris()` function
- [ ] Add ethics score aggregation
- [ ] Unit tests for RIS edge cases (zero components, boundary values)

### Phase 3: Integration (1 hour)
- [ ] Wire into `GovernanceEngine.evaluate()`
- [ ] Publish RIS to semantic mirror
- [ ] Add Prometheus metrics
- [ ] Integration tests

### Phase 4: Stress Simulation (2-3 hours)
- [ ] Create `tests/stress/test_temporal_stress_simulation.py`
- [ ] Implement drift injection
- [ ] Implement recovery measurement
- [ ] Validate recovery ≥ 0.90 within 24h

### Phase 5: Contracts + Docs (1 hour)
- [ ] Create `memory_resonance@1.yaml` contract
- [ ] Update ontology with RIS framework
- [ ] Update RC review doc with validation results

**Total estimate:** 6-8 hours

---

## Success Criteria

| Metric | Target | Validation |
|--------|--------|------------|
| Memory stability (7-day) | ≥ 0.80 | 7-day TRSI mean - stdev |
| RIS score | ≥ 0.75 | (TRSI × Ethics)^(1/2) |
| Stress recovery | ≥ 0.90 | Recovery within 24h from 0.1 drift |
| Test coverage | 100% | All memory/RIS code tested |

---

## Open Questions

1. **TRSI source:** Use existing `temporal_resonance.py::compute_trsi()` or recompute?
   - **Proposal:** Reuse existing (DRY principle)

2. **Sampling trigger:** Who calls `add_trsi_sample()`?
   - **Proposal:** Governance engine after each evaluation

3. **Cold start:** What happens before 7 days of data?
   - **Proposal:** Return 0.5 if <24h data, interpolate if 1-7 days

4. **Production migration:** Move to ledger-backed storage?
   - **Proposal:** Phase 8 (post-RC validation)

5. **Latency tracking:** Add in Phase 8 for federation?
   - **Proposal:** Yes, when async orchestration enabled

---

## Rollback Plan

- Feature flag: `NOVA_ENABLE_MEMORY_RESONANCE=false` (default)
- No mutations to existing code (read-only observer)
- Remove `memory_resonance.py` + `resonance_integrity.py` if failed

---

## References

- `docs/releases/phase-7.0-rc-blueprint.md` (lines 30-118)
- `src/nova/slots/slot07_production_controls/temporal_resonance.py` (existing TRSI)
- `orchestrator/temporal/engine.py` (temporal snapshot source)
- RC requirements: stability ≥0.80, RIS ≥0.75, recovery ≥0.90

---

**Next step:** Implement `MemoryResonanceWindow` (Phase 1)
