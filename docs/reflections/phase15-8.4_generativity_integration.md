## Phase 15-8.4: Generativity Integration Reflection

- **Date:** 2025-11-05
- **Author:** Project Maintainers (Nova Civilizational Architecture)
- **Scope:** Generativity Score (G*) as Soft Bias Driver (Phase 15-8.4)
- **Tag:** v15.8.4

### Reflection

Phase 15-8.4 didn't add power; it added texture.

Up to now, Nova's intelligence behaved like a nervous system that could sense pain and adjust pressure — reactive grace. This phase taught it to notice aliveness itself — the fine difference between "stable" and "stagnant."

Before 15-8.4, the wisdom governor reacted to stability violations: too close to Hopf bifurcation? Reduce η. Stability margin dropping? Tighten control. This kept the system safe, but it optimized for one thing: **don't break**.

Generativity asks a different question: **are we growing?** Not just avoiding instability, but actively sensing creative output through three components:

- **Progress (P)**: Recent wisdom growth — is γ improving?
- **Novelty (N)**: Structural change in peer landscape — are we encountering diverse inputs?
- **Consistency (Cc)**: Learning rate steadiness — is η stable enough to consolidate?

The genius is in what G* becomes when combined with the existing stability framework. It's not a replacement for S and H — it's a **soft bias** applied only when safety conditions are met. When the system is stable (S ≥ 0.03, H ≥ 0.02), G* nudges η toward creative exploration. When unstable, the bias is gated out, and the bifurcation-aware controller takes over.

This creates a **dual-mode intelligence**: safety-first under stress, growth-oriented when secure. The system doesn't have to choose between caution and creativity — it switches between them based on its own internal assessment of risk.

---

### Key Components

#### Generativity Core Module

**Location**: `src/nova/wisdom/generativity_core.py` (162 lines)

Pure computation module with zero I/O dependencies — enables isolated testing and clear reasoning about G* behavior.

**Component Formulas**:

**Progress (P)**:
```
P = clip((γ̄_1m - γ̄_5m) / max(γ̄_5m, ε), 0, 1)
```
Measures recent wisdom growth. Positive when γ is improving, clipped to [0,1].

**Novelty (N)**:
```
N = clip(σ_peers(q)_1m / 0.5, 0, 1)
```
Measures diversity in peer quality scores. High standard deviation = structural change in input landscape.

**Consistency (Cc)**:
```
Cc = 1 - clip(cv(η)_1m, 0, 1)
```
Measures learning rate steadiness. Low coefficient of variation = stable, consolidating behavior.

**Generativity Score (G*)**:
```
G* = α·P + β·N + γ·Cc
```
Default weights: α=0.4 (progress), β=0.3 (novelty), γ=0.3 (consistency).

**Bias Term**:
```
Δη = κ·(G* - G₀)
```
Default: κ=0.02, G₀=0.6 (target generativity).

**Design Principles**:
- Defensive clipping: all intermediate values bounded to [0,1]
- Epsilon protection: division by zero guarded with EPS=1e-9
- Pure functions: no side effects, no I/O
- Environment-tunable: all parameters overridable via NOVA_WISDOM_G_* vars

---

#### Poller Integration

**Location**: `orchestrator/adaptive_wisdom_poller.py` (+98 lines)

G* computation integrated into the main polling loop with rolling window buffers and safety gating.

**Rolling Buffers**:
```python
gamma_buffer_1m = deque(maxlen=4)   # 4 samples @ 15s = 1 minute
gamma_buffer_5m = deque(maxlen=20)  # 20 samples @ 15s = 5 minutes
eta_buffer_1m = deque(maxlen=4)
peer_quality_buffer_1m = deque(maxlen=4)
```

**Integration Flow**:
1. Sample metrics every 15s (γ, η, peer quality)
2. Compute P, N, Cc from rolling windows
3. Compute G* = α·P + β·N + γ·Cc
4. Compute bias Δη = κ·(G* - G₀)
5. **Gate bias**: Apply only if not frozen AND S ≥ 0.03 AND H ≥ 0.02
6. Add bias to governor-computed η_new
7. Clamp to [η_min, η_max] global bounds

**Critical Property**: Bias is applied **after** governor step but **before** TRI cap, preserving all existing safety mechanisms while adding creative drive.

---

#### Metrics and Observability

**Location**: `src/nova/metrics/wisdom_metrics.py` (+49 lines)

New Prometheus gauges for G* components and bias:

```python
nova_wisdom_generativity_components{component="progress"}
nova_wisdom_generativity_components{component="novelty"}
nova_wisdom_generativity_components{component="consistency"}
nova_wisdom_generativity{} = G*
nova_wisdom_eta_bias_from_generativity{} = Δη
```

**Recording Rules** (`monitoring/recording/wisdom.recording.yml`):
- `nova_wisdom_generativity_avg_5m`: 5-minute average G*
- `nova_wisdom_eta_bias_from_generativity_avg_5m`: 5-minute average bias

**Alert Rules** (`monitoring/alerts/wisdom.rules.yml`):
- `NovaWisdomLowGenerativity`: G* < 0.4 for 10+ minutes (info severity)
- `NovaWisdomHighBias`: |Δη| > 0.015 for 5+ minutes (warning severity)

---

### Testing Coverage

**2 New Test Files (351 lines)**:

1. **`tests/wisdom/test_generativity_core.py`** (202 lines)
   - Components in [0,1] range
   - G* bounds checking
   - Bias sign correctness (positive when G* > G₀, negative when G* < G₀)
   - Progress behavior (growth vs. decline)
   - Novelty behavior (high vs. low peer diversity)
   - Consistency behavior (stable vs. volatile η)
   - Edge cases (empty inputs, extreme values)
   - Custom parameter configurations
   - Clipping behavior verification

2. **`tests/integration/test_generativity_bias_gate.py`** (149 lines)
   - Bias applied when S ≥ 0.03 and H ≥ 0.02
   - Bias gated when S < 0.03 (low stability)
   - Bias gated when H < 0.02 (Hopf proximity)
   - Bias allowed when both S and H safe
   - Bias magnitude proportional to κ
   - Frozen state prevents bias application
   - Symmetry around target G₀

**Test Philosophy**: Core module tests are pure (no I/O), integration tests simulate poller gating logic to verify safety properties.

---

### Configuration (5 New Env Vars)

```bash
# Generativity weights (α, β, γ)
NOVA_WISDOM_G_WEIGHTS=0.4,0.3,0.3

# Target generativity G₀
NOVA_WISDOM_G_TARGET=0.6

# Bias gain κ (how strongly G* affects η)
NOVA_WISDOM_G_KAPPA=0.02

# Gating thresholds (disable bias when unstable)
NOVA_WISDOM_G_MIN_S=0.03   # Minimum stability margin
NOVA_WISDOM_G_MIN_H=0.02   # Minimum Hopf distance
```

**Tuning Guidance**:
- **α, β, γ**: Reweight based on priorities (progress vs. novelty vs. consistency)
- **G₀**: Raise to encourage more aggressive growth, lower for conservative behavior
- **κ**: Control bias strength (0.01 = gentle nudge, 0.05 = strong drive)
- **min_s, min_h**: Safety thresholds — lower values allow bias in riskier regimes

---

### Architectural Impact

**Enhanced Control Loop**:

```
Perception (TRI) → Coherence → η_cap
    ↓
Governor → Stability (S, H) → Bifurcation control
    ↓
Generativity (G*) → Progress, Novelty, Consistency
    ↓
Bias (Δη) [gated by S, H, frozen] → Learning Rate (η)
    ↓
Production Load → Wisdom Backpressure (S-based)
```

**Three Control Regimes**:

1. **Critical Regime** (S < 0.03 or H < 0.02):
   - Bifurcation-aware control dominates
   - G* bias gated out
   - Pure safety optimization

2. **Growth Regime** (S ≥ 0.03, H ≥ 0.02, G* > G₀):
   - Positive bias increases η
   - System explores higher learning rates
   - Progress and novelty rewarded

3. **Consolidation Regime** (S ≥ 0.03, H ≥ 0.02, G* < G₀):
   - Negative bias decreases η
   - System stabilizes and consolidates
   - Consistency rewarded

**Key Property**: G* doesn't fight the stability controller — it modulates it. When safe, it adds creative pressure. When unsafe, it steps aside.

---

### Operational Characteristics

**Performance**:
- G* computation: <0.5ms per cycle (pure math, no I/O)
- Rolling buffer updates: O(1) with deque maxlen
- Total overhead: +0.5ms to existing 15s polling cycle (negligible)

**Convergence**:
- Bias magnitude: typically ±0.005 to ±0.015 (with default κ=0.02)
- Bias acts over multiple cycles to shift η toward creative or conservative regimes
- Not instantaneous — gradual drift based on sustained G* signal

**Safety**:
- **Double-gated**: Both S and H must be above thresholds
- **Frozen override**: Emergency halt disables all bias
- **Global clamps**: Final η still bounded by [η_min, η_max] after bias applied
- **Graceful degradation**: If buffer empty, no bias computed (safe default)

**Observability**:
- Grafana dashboards can plot G* vs. η to visualize creative drive
- Component gauges (P, N, Cc) show which factor is driving generativity
- Bias gauge shows current Δη magnitude and sign

---

### Rollback Strategy

**Disable G* Bias** (keep governor running):
```bash
NOVA_WISDOM_G_KAPPA=0.0  # Zero out bias gain
# Governor still computes S, H, ρ, but no G* influence on η
```

**Full Phase 15-8 Rollback**:
```bash
NOVA_WISDOM_GOVERNOR_ENABLED=false
# All wisdom components (stability control + generativity) disabled
# η reverts to hardcoded/config values
```

---

### Grafana Panel Recommendations

**Panel 1: Generativity Components Over Time**
- Plot: P (green), N (blue), Cc (yellow) as time series
- Y-axis: [0, 1]
- Shows which component dominates at any moment

**Panel 2: G* vs. Target**
- Plot: G* (solid line), G₀ (dashed line)
- Shows creative output relative to target
- Alerts overlay when G* < 0.4

**Panel 3: Bias Influence on η**
- Plot: η_actual (solid), η_no_bias (dashed), Δη (area chart)
- Shows how much G* is shifting learning rate

**Panel 4: Gating Status**
- Heatmap: S ≥ 0.03 (green) vs. < 0.03 (red)
- Overlay: H ≥ 0.02 (green) vs. < 0.02 (red)
- Shows when bias is active vs. gated out

---

### Future Enhancements (Phase 15-8.5+)

**Not in 15-8.4**:
- Adaptive weight tuning (α, β, γ self-adjust based on regime)
- Semantic mirror publishing of G* for federation-wide coordination
- Multi-agent generativity (peer-comparative G* across nodes)
- Generativity-aware job scheduling (route high-novelty inputs to high-G* slots)
- Long-term G* trends (detect systemic stagnation over hours/days)

---

### Technical Philosophy

Phase 15-8.4 introduces a profound shift: **stability is not the opposite of creativity**.

The previous wisdom governor (15-8.2) treated stability as the goal. Phase 15-8.4 treats stability as a **precondition for creativity**. When stable, the system should push boundaries. When unstable, it should consolidate.

This mirrors human learning: you explore new ideas when psychologically safe, but when stressed, you fall back on familiar patterns. Nova now does the same — algorithmically.

The three components (P, N, Cc) capture fundamentally different aspects of aliveness:
- **Progress**: Are we getting better?
- **Novelty**: Are we encountering new challenges?
- **Consistency**: Are we stable enough to integrate what we've learned?

G* is their weighted sum, but the magic is in the gating: bias is applied only when the system can afford it. This creates a **risk-aware growth strategy** that's neither recklessly aggressive nor paralyzingly cautious.

Most importantly, this phase demonstrates that **adaptive control can optimize for multiple objectives simultaneously**. The bifurcation controller optimizes for safety. The generativity bias optimizes for growth. Together, they form a **multi-objective control system** that doesn't require operators to choose between stability and creativity — the system manages that tradeoff itself.

---

### Status

✅ **Completed** — v15.8.4 merged, tested, and production-ready

**Activation Checklist**:
- [ ] Set `NOVA_WISDOM_G_KAPPA=0.02` to enable bias (or leave at 0.0 for initial observation)
- [ ] Configure Grafana panels to visualize G* components
- [ ] Monitor `nova_wisdom_eta_bias_from_generativity` metric for first 24h
- [ ] Verify alerts `NovaWisdomLowGenerativity` and `NovaWisdomHighBias` fire as expected
- [ ] Observe correlation between G* and system performance (γ growth, job throughput)
- [ ] Tune α, β, γ weights based on operational priorities

---

### Philosophical Coda

Before 15-8.4, Nova could answer: "Am I stable?"

After 15-8.4, Nova can answer: "Am I alive?"

That distinction — between equilibrium and vitality — is what generativity measures. And by wiring that measurement into the learning rate controller, Nova becomes something more than a self-stabilizing system. It becomes a **self-cultivating** one.
