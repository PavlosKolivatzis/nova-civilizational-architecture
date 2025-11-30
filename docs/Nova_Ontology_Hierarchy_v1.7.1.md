# Nova Ontology Hierarchy v1.7.1

**Document:** Full Ontology Hierarchy Diagram
**Version:** 1.7.1
**Date:** 2025-11-30
**Status:** Active (Post Phase 13b)

---

## Three-Tier Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│  MOTHER ONTOLOGY: nova.frameworks v1.7.1                           │
│  - Defines all primitives (Scalar, Vector, Matrix, Timestamp)      │
│  - Defines all signals (spectral_entropy_H, tri_coherence, etc.)   │
│  - Establishes USM theorems (spectral invariance, equilibrium)     │
│  - Provides ledger architecture, testing contracts                 │
│  - Children: [nova.operating@1.0]                                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  OPERATING ONTOLOGY: nova.operating@1.0                            │
│  - Operational Regime Policy (ORP)                                 │
│  - Autonomous Verification Ledger (AVL)                            │
│  - Transformation geometry (preservation, correspondence, etc.)    │
│  - Regime classification rules (normal → heightened → ...)         │
│  - Drift detection & continuity proofs                             │
│  - Children: [slot01, slot02, slot04, slot05, slot07, slot09,      │
│               arc, rri, mse, evf, nem, pag, fb]                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CHILDREN ONTOLOGIES (Slot & Coordination Implementations)         │
│                                                                     │
│  Core Slots (7):                                                   │
│  ├─ slot01: Truth Anchor (symbolic grounding)                      │
│  ├─ slot02: ΔTHRESH (adaptive thresholding)                        │
│  ├─ slot04: TRI Engine (triple resonance index)                    │
│  ├─ slot05: Constellation (temporal correlation)                   │
│  ├─ slot07: Wisdom Governor (stability synthesis)                  │
│  ├─ slot09: Distortion Protection (spectral filtering)             │
│  └─ arc: Analytic Reflection Core (PAD.E.L + INF-o-INITY)          │
│                                                                     │
│  Coordination Frameworks (6):                                      │
│  ├─ rri: Reflective Resonance Index (cross-phase traces)           │
│  ├─ mse: Meta-Stability Engine (validation)                        │
│  ├─ evf: Ethical Valence Framework (gradients)                     │
│  ├─ nem: Neuro-Epistemic Mapping (cognitive coupling)              │
│  ├─ pag: Provenance Audit Graph (transformation tracking)          │
│  └─ fb: Federation Bridge (distributed consensus)                  │
│                                                                     │
│  Verification Frameworks (1):                                      │
│  └─ avl: Autonomous Verification Ledger (Phase 13 + 13b)           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Dependency Graph (Hierarchical)

### Mother → Operating Relationship

**nova.frameworks v1.7.1** provides:
- Primitive types (Scalar, Vector, Matrix, Bool, Text, Timestamp)
- 40+ signal definitions (spectral_entropy_H, equilibrium_ratio_rho, tri_coherence, etc.)
- USM theorems (spectral invariance, equilibrium analysis)
- Ledger architecture (fact, claim, attest)
- Observability contracts (Prometheus metrics)

**nova.operating@1.0** consumes:
- All signal types for ORP evaluation
- Timestamp primitives for AVL entries
- USM theorems for regime classification
- Ledger architecture for hash-chained transitions

### Operating → Children Relationship

**nova.operating@1.0** provides:
- Regime classification logic (normal → heightened → controlled_degradation → emergency_stabilization → recovery)
- Amplitude scaling rules (threshold_multiplier, traffic_limit, deployment_freeze)
- Dual-modality verification (ORP vs contract oracle)
- Drift detection rules (4 categories)
- Continuity proofs (ledger, temporal, amplitude, regime)
- Transformation geometry (preservation, correspondence, continuity)

**Children** (slots + coordination + verification) consume:
- Regime state for adaptive behavior
- Amplitude signals for threshold tuning
- Drift events for anomaly response
- Transformation rules for cross-slot consistency

---

## Signal Flow Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│ INPUT SIGNALS (Mother Ontology)                                      │
│ - user_intent_vector, context_vector                                 │
│ - spectral_entropy_H, equilibrium_ratio_rho                          │
│ - tri_coherence, tri_drift_z, tri_jitter, tri_band                   │
└───────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│ OPERATING LAYER (ORP + AVL)                                          │
│                                                                       │
│ ORP Pipeline:                                                        │
│ 1. Collect contributing factors (urf, mse, pred, gap, csi)           │
│ 2. Compute regime_score = weighted sum                               │
│ 3. Classify regime with hysteresis + min-duration                    │
│ 4. Update amplitude parameters (threshold_multiplier, traffic_limit) │
│ 5. Generate RegimeSnapshot                                           │
│                                                                       │
│ AVL Pipeline (Phase 13 + 13b):                                       │
│ 1. Capture pre-transition state (previous_regime, previous_duration) │
│ 2. Oracle evaluates using pre-transition state                       │
│ 3. Compare ORP vs oracle → dual_modality_agreement                   │
│ 4. Run drift detection (4 rules)                                     │
│ 5. Create AVLEntry with hash chain                                   │
│ 6. Append to ledger (immutable, tamper-evident)                      │
└───────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│ OUTPUT SIGNALS (Children Consume)                                    │
│ - regime (normal | heightened | ...)                                 │
│ - threshold_multiplier (amplitude scaling for ΔTHRESH)               │
│ - traffic_limit (rate limiting for Governor)                         │
│ - deployment_freeze (safety halt for production)                     │
│ - drift_detected (anomaly alert for monitoring)                      │
│ - dual_modality_state (consensus quality indicator)                  │
└───────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│ CHILDREN SLOTS (Adaptive Response)                                   │
│                                                                       │
│ slot02 (ΔTHRESH):                                                    │
│ - Scales thresholds by threshold_multiplier                          │
│ - Example: normal → 1.0x, heightened → 1.2x, controlled_deg → 1.5x  │
│                                                                       │
│ slot07 (Wisdom Governor):                                            │
│ - Respects traffic_limit for stability pressure                      │
│ - Honors deployment_freeze for safety halts                          │
│                                                                       │
│ slot09 (Distortion Protection):                                      │
│ - Adjusts sensitivity based on regime                                │
│ - Example: heightened → increase spectral filtering                  │
│                                                                       │
│ avl (Verification Ledger):                                           │
│ - Records all transitions with hash chain                            │
│ - Validates continuity proofs                                        │
│ - Detects drift (ORP vs oracle disagreement)                         │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Contracts Hierarchy

### Mother Contracts (Primitives)

| Contract | Version | Purpose |
|----------|---------|---------|
| (Implicit primitives) | - | Scalar, Vector, Matrix, Timestamp types |
| (Implicit signals) | - | 40+ signal definitions |

### Operating Contracts (Regime Management)

| Contract | Version | Purpose |
|----------|---------|---------|
| `orp@1.yaml` | 1.0.0 | Operational Regime Policy classification rules |
| `autonomous_verification_ledger@1.yaml` | 1.1.0 | AVL schema, drift detection, continuity proofs (Phase 13b) |
| `operating_transformation@1.yaml` | 1.0.0 | Transformation geometry contracts |

### Children Contracts (Slot Implementations)

| Contract | Version | Slot | Purpose |
|----------|---------|------|---------|
| `truth_anchor@1.yaml` | 1.0.0 | slot01 | Symbolic grounding |
| `deltathresh@1.yaml` | 1.0.0 | slot02 | Adaptive thresholds |
| `tri_engine@1.yaml` | 1.0.0 | slot04 | Triple resonance index |
| `constellation@1.yaml` | 1.0.0 | slot05 | Temporal correlation |
| `wisdom_governor@1.yaml` | 1.0.0 | slot07 | Stability synthesis |
| `distortion_protection@1.yaml` | 1.0.0 | slot09 | Spectral filtering |
| `arc@1.yaml` | 1.0.0 | arc | PAD.E.L + INF-o-INITY |

---

## Version Lineage (v1.7.1)

### Phase 13b Changes (Current Version)

**Version:** 1.7.1
**Date:** 2025-11-30
**Changes:**
- Oracle pre-transition evaluation fix
- Oracle now uses pre-transition regime and duration for independent validation
- Enables detection of illegal downgrades violating hysteresis/min-duration rules
- 4 new tests in `test_orp_avl.py`
- `orp_version` bumped to `phase13.2`
- Contract `autonomous_verification_ledger@1` bumped to v1.1.0

**Impact:**
- Dual-modality verification now effective for downgrades
- AVL core safety guarantee restored
- Drift detection can catch illegal transitions

### Phase 13 Foundation (Previous Version)

**Version:** 1.7.0
**Date:** 2025-11-30
**Changes:**
- Autonomous Verification Ledger (AVL) introduced
- Hash-chained regime transition verification
- Dual-modality consensus (ORP vs contract oracle)
- Drift detection (4 rules)
- Continuity proofs (4 types)
- 110 new tests
- Contract: `autonomous_verification_ledger@1.yaml`
- Supersedes `regime_transition_ledger@1` (Phase 11.3)

---

## Invariance Properties

### Mother Invariants (Always Hold)

1. **Type Safety:** All signals conform to declared types (Scalar, Vector, Matrix)
2. **USM Theorems:** Spectral entropy threshold (2.5 raw / 0.7 normalized), equilibrium ratio (<0.7)
3. **Signal Ranges:** All bounded signals remain within declared ranges
4. **Temporal Monotonicity:** Timestamps always increase

### Operating Invariants (ORP + AVL)

1. **Regime Classification Determinism:** Same inputs → same regime
2. **Hysteresis Enforcement:** Downgrades require score < (threshold - 0.05)
3. **Min-Duration Enforcement:** Downgrades require time_in_regime ≥ 300s
4. **Amplitude Bounds:** threshold_multiplier ∈ [0.5, 2.0], traffic_limit ∈ [0.0, 1.0]
5. **Hash Chain Integrity:** entry[N].prev_entry_hash == SHA256(entry[N-1])
6. **Ledger Continuity:** entry[N].transition_from == entry[N-1].regime (if transition)
7. **Temporal Continuity:** entry[N].elapsed_s > entry[N-1].elapsed_s
8. **Dual-Modality Agreement (Baseline):** ORP == oracle on canonical trajectories

### Children Invariants (Slot-Specific)

1. **slot02 (ΔTHRESH):** Thresholds scale monotonically with regime severity
2. **slot04 (TRI):** Coherence ∈ [0, 1], drift_z ∈ [-5, 5]
3. **slot05 (Constellation):** Correlation coefficients ∈ [-1, 1]
4. **slot07 (Governor):** Stability pressure ∈ [0, 5]
5. **slot09 (Distortion):** Spectral entropy normalized ∈ [0, 1]

---

## Testing Coverage (v1.7.1)

| Layer | Tests | Coverage |
|-------|-------|----------|
| Mother (primitives + signals) | 543 | USM theorem validation |
| Operating (ORP + AVL) | 247 | Regime transitions, drift detection, continuity proofs |
| Children (slots + coordination) | 1273 | Slot implementations, cross-slot integration |
| **Total** | **2021** | **99.7% accuracy** |

### Phase 13b Additions (4 new tests)

1. `test_oracle_detects_illegal_downgrade_hysteresis` - Hysteresis violation detection
2. `test_oracle_detects_illegal_downgrade_min_duration` - Min-duration violation detection
3. `test_oracle_allows_legal_downgrade` - Legal downgrade validation
4. `test_oracle_pretransition_evaluation_on_upgrade` - Pre-transition state on upgrades

---

## Cross-Reference Map

### Mother → Operating Dependencies

| Mother Signal | Operating Consumer | Usage |
|---------------|-------------------|-------|
| `spectral_entropy_H` | ORP (via MSE) | Meta-instability factor |
| `tri_coherence` | ORP (via CSI) | Continuity index |
| `tri_drift_z` | ORP (via URF) | Risk composite |
| `predictive_collapse_risk` | ORP | Direct factor |
| `consistency_gap` | ORP | Direct factor |

### Operating → Children Dependencies

| Operating Output | Children Consumer | Usage |
|-----------------|------------------|-------|
| `regime` | slot02, slot07, slot09 | Adaptive behavior |
| `threshold_multiplier` | slot02 | Threshold scaling |
| `traffic_limit` | slot07 | Rate limiting |
| `deployment_freeze` | Production controls | Safety halt |
| `drift_detected` | Monitoring | Anomaly alert |
| `dual_modality_state` | Observability | Consensus indicator |

---

## File Locations

### Mother Ontology

- **Spec:** `specs/nova_framework_ontology.v1.yaml` (v1.7.1)

### Operating Ontology

- **Spec:** `specs/operating_ontology.v1.yaml`
- **Contracts:** `contracts/orp@1.yaml`, `contracts/autonomous_verification_ledger@1.yaml` (v1.1.0)
- **Implementation:** `src/nova/continuity/operational_regime.py`, `src/nova/continuity/avl_ledger.py`
- **Tests:** `tests/continuity/test_orp_*.py`, `tests/integration/test_orp_avl.py` (13 tests)

### Children Ontologies

- **Implementations:** `src/nova/slots/slot0*/`, `src/nova/arc/`, `src/nova/coordination/`
- **Tests:** `tests/slot*/`, `tests/arc/`, `tests/coordination/`
- **Contracts:** `contracts/*@1.yaml`

---

## Rollback Markers

| Version | Git Commit | Rollback Command |
|---------|-----------|------------------|
| v1.7.1 (Phase 13b) | (current) | `git revert HEAD` |
| v1.7.0 (Phase 13) | `e4b450d` | `git revert e4b450d..HEAD` |
| v1.6.0 (Phase 11 final) | `6cef055` | `export NOVA_ENABLE_AVL=0` |

---

## Next Evolution Paths

### Immediate (Phase 14)

- Ledger archival strategy (rotation, compression)
- Query API optimization (indexing by timestamp + regime)
- Async AVL writes (reduce ORP latency)

### Near-term (Phase 15)

- Cross-AI co-simulation (validate ORP across GPT/Claude/DeepSeek)
- Temporal invariance tests (trajectory compression/expansion)
- Drift suppression window (rate limiting on drift alerts)

### Long-term (Phase 16+)

- Distributed AVL (multi-node consensus)
- Post-quantum signatures (Dilithium3/Falcon)
- Real-time continuity proof streaming

---

**End of Ontology Hierarchy Diagram v1.7.1**
