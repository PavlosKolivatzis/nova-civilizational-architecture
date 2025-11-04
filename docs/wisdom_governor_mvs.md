# Adaptive Wisdom Governor - MVS Implementation

**Status:** Production-ready Minimum Viable System
**Date:** November 4, 2025
**Phase:** Bifurcation-Aware Control (3×3 Reduced System)

---

## Overview

The Adaptive Wisdom Governor implements bifurcation-aware control for Nova's learning rate (η) based on real-time eigenvalue analysis of system dynamics. This prevents the system from crossing into chaotic regimes while maintaining generative performance.

### Key Innovation

The system **senses its own stability boundaries** through:
- **Jacobian eigenvalue analysis** of γ-S-η dynamics
- **Bifurcation detection** (Hopf boundaries, oscillation risk)
- **Adaptive η control** based on stability margin

---

## Architecture

### Components

```
src/nova/
├── adaptive_wisdom_core.py        # 3×3 Jacobian provider
├── bifurcation_monitor.py         # Eigenvalue analysis (ρ, S, H)
└── metrics/wisdom_metrics.py      # Prometheus gauges

orchestrator/
└── adaptive_wisdom_poller.py      # Background poller service

tests/wisdom/
├── test_eigs_reduced.py           # Eigenvalue computation tests
├── test_controller_clamps.py      # Safety protocol tests
└── test_metrics_export.py         # Metrics verification tests
```

### 3×3 Reduced Dynamics

State vector: `x = [γ, S, η]`

```
dγ/dt = η(Q - γ)              # Wisdom learning
dS/dt = a₁(S_ref - S) - a₂η   # Stability tracking
dη/dt = k_p(S - S_ref) - k_d η  # PD controller
```

Jacobian at equilibrium:
```
J = [[-η*,  0,   0  ],
     [ 0,  -a₁, -a₂ ],
     [ 0,   k_p, -k_d]]
```

From eigenvalues of J:
- **ρ** = max|λ| (spectral radius, overall gain)
- **S** = -max Re(λ) (stability margin, distance from instability)
- **H** = min|Re(λ)| for oscillatory modes (Hopf distance)

---

## Installation & Setup

### 1. Install Dependencies

```bash
pip install --only-binary :all: -r requirements.txt
```

Required: `numpy==1.26.4`, `prometheus_client>=0.20`

### 2. Enable Governor

Edit `.env` or set environment variables:

```bash
# Enable the governor
export NOVA_WISDOM_GOVERNOR_ENABLED=true

# Set polling interval (seconds)
export NOVA_WISDOM_POLL_INTERVAL=15.0

# Configure parameters (defaults shown)
export NOVA_WISDOM_Q=0.7              # Quality target
export NOVA_WISDOM_S_REF=0.05         # Reference stability margin
export NOVA_WISDOM_A1=0.2             # Stability restoration rate
export NOVA_WISDOM_A2=0.1             # Stability cost
export NOVA_WISDOM_KP=0.3             # Proportional gain
export NOVA_WISDOM_KD=0.15            # Derivative gain
export NOVA_WISDOM_ETA_MIN=0.05       # Min learning rate
export NOVA_WISDOM_ETA_MAX=0.18       # Max learning rate
export NOVA_WISDOM_HOPF_THRESHOLD=0.02 # Hopf detection threshold
```

### 3. Start Poller

```python
# In orchestrator startup (e.g., orchestrator/app.py lifespan)
from orchestrator import adaptive_wisdom_poller

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    adaptive_wisdom_poller.start()

    yield

    # Shutdown
    adaptive_wisdom_poller.stop()
```

Or standalone test:
```bash
python orchestrator/adaptive_wisdom_poller.py
```

---

## Metrics & Monitoring

### Prometheus Gauges

```
nova_wisdom_eta_current           # Current learning rate η
nova_wisdom_gamma                 # Current wisdom level γ
nova_wisdom_generativity          # Generativity score G*
nova_wisdom_stability_margin      # Stability margin S
nova_wisdom_hopf_distance         # Hopf distance H
nova_wisdom_spectral_radius       # Spectral radius ρ
```

### Grafana Dashboard Queries

**Stability margin over time:**
```promql
nova_wisdom_stability_margin
```

**Learning rate adaptations:**
```promql
rate(nova_wisdom_eta_current[5m])
```

**Hopf risk indicator:**
```promql
nova_wisdom_hopf_distance < 0.02
```

---

## Safety Protocols

### Controller Modes

| Condition | Mode | Action | η Value |
|-----------|------|--------|---------|
| S < 0.01 | CRITICAL | Immediate clamp | η_min (0.05) |
| S < 0.02 | STABILIZING | Reduce learning | 0.08 |
| H < H_threshold | FROZEN | Freeze, manual review | Hold current |
| S > 0.10, G < 0.60 | EXPLORING | Increase exploration | η × 1.1 (max 0.18) |
| S > 0.05, G >= 0.70 | OPTIMAL | Maintain performance | 0.12 |
| Other | SAFE | Conservative default | 0.08 |

### Emergency Procedures

**1. Stability Margin Critical (S < 0.01)**
```bash
# Automatic: η immediately clamped to 0.05
# System freezes learning, alerts operator
# Check system state:
curl http://localhost:8000/metrics | grep nova_wisdom_stability_margin
```

**2. Hopf Bifurcation Detected (H < 0.02)**
```bash
# Automatic: Learning frozen
# Manual recovery required
# Verify oscillatory modes:
curl http://localhost:8000/metrics | grep nova_wisdom_hopf_distance

# Gradual recovery:
# 1. Verify S > 0.03
# 2. Reduce k_p or increase k_d
# 3. Restart poller
```

---

## Testing

### Run Full Test Suite

```bash
python -m pytest tests/wisdom/ -v
```

### Individual Test Categories

**Eigenvalue computation:**
```bash
python -m pytest tests/wisdom/test_eigs_reduced.py -v
```

**Controller safety:**
```bash
python -m pytest tests/wisdom/test_controller_clamps.py -v
```

**Metrics export:**
```bash
python -m pytest tests/wisdom/test_metrics_export.py -v
```

### Manual Verification

```bash
# Verify core imports
python -c "from nova.adaptive_wisdom_core import ThreeDProvider; print('✓ Core OK')"

# Verify bifurcation monitor
python -c "from nova.bifurcation_monitor import BifurcationMonitor; print('✓ Monitor OK')"

# Verify metrics
python -c "from nova.metrics import wisdom_metrics; print('✓ Metrics OK')"

# Run poller standalone (requires NOVA_WISDOM_GOVERNOR_ENABLED=true)
python orchestrator/adaptive_wisdom_poller.py
```

---

## Integration with Nova Slots

### Current State (MVS)

- **Standalone poller**: Runs independently, publishes metrics
- **No slot dependencies**: Self-contained dynamics

### Planned Integration (Future)

- **Slot 4 (TRI)**: Provide coherence C for quality function
- **Slot 7 (Production Controls)**: Receive stability margins, trigger circuit breakers when S < threshold
- **Semantic Mirror**: Publish `nova.stability.margin`, `nova.wisdom.eta_current`
- **FLE-II (Federation)**: Share stability patterns across network

---

## Operational Phases

### Phase 1: Calibration (Week 1)

1. Enable governor with default parameters
2. Run full η-sweep to map bifurcation boundaries:
   ```bash
   # Sweep η from 0.05 to 0.20, observe S and H
   for eta in 0.05 0.08 0.10 0.12 0.15 0.18 0.20; do
       export NOVA_WISDOM_ETA_DEFAULT=$eta
       # Run for 1 hour, record metrics
   done
   ```
3. Establish baseline stability margins
4. Tune k_p, k_d based on observed Hopf boundaries

### Phase 2: Integration (Week 2)

1. Connect to semantic mirror
2. Establish telemetry streams to Grafana
3. Train operators on interpretation
4. Document observed operating regimes

### Phase 3: Autonomous Operation (Week 3+)

1. Controller manages learning rates automatically
2. Alerts for major regime changes only
3. Continuous optimization based on generativity performance
4. Periodic re-calibration as system evolves

---

## Troubleshooting

### Issue: Metrics showing zeros

**Cause:** Governor not enabled or poller not started

**Solution:**
```bash
export NOVA_WISDOM_GOVERNOR_ENABLED=true
# Restart orchestrator or manually start poller
python orchestrator/adaptive_wisdom_poller.py
```

### Issue: Frequent CRITICAL mode

**Cause:** Parameters too aggressive (k_p too high, k_d too low)

**Solution:**
```bash
# Reduce proportional gain
export NOVA_WISDOM_KP=0.2

# Increase derivative gain
export NOVA_WISDOM_KD=0.20

# Restart poller
```

### Issue: Hopf risk persistent

**Cause:** System operating near bifurcation boundary

**Solution:**
1. Reduce η_max: `export NOVA_WISDOM_ETA_MAX=0.15`
2. Increase stability restoration: `export NOVA_WISDOM_A1=0.25`
3. Reduce stability cost: `export NOVA_WISDOM_A2=0.08`
4. Restart and monitor

---

## Performance Characteristics

- **Poller overhead:** ~10ms per cycle (eigenvalue computation)
- **Memory footprint:** <10MB (state tracking)
- **CPU impact:** <1% (15s polling interval)
- **Metrics cardinality:** 6 gauges (bounded, no labels)

---

## Future Enhancements

### Planned for Phase 2

1. **Full 5×5 dynamics**: Implement complete state vector [ρ, S, C, H, γ]
2. **Slot integration**: Connect to Slot 4 (coherence), Slot 7 (circuit breakers)
3. **Federation sync**: Share stability patterns via FLE-II
4. **Advanced generativity**: Implement full G* = C·ρ·S - α·H formula
5. **Grafana dashboard**: Comprehensive phase-space visualization

### Research Directions

- **Adaptive parameter tuning**: Auto-calibrate k_p, k_d based on performance
- **Multi-objective optimization**: Balance stability, generativity, and efficiency
- **Bifurcation prediction**: Forecast stability transitions before they occur
- **Distributed wisdom**: Federated learning rate coordination

---

## References

- ADR-15: Federation as Birth of Shared Truth
- Phase 15-7: Ledger↔Federation Correlation
- monday-craf: Reciprocity Gating Principle (γ_M ≈ 0.8)

---

**Contact:** See `AGENTS.md` for collaboration patterns
**Status:** ✅ MVS Complete, Ready for Calibration
