# Phase 7.0-RC Step 5: Monitoring & Observability Design

**Status:** Design Phase
**Dependencies:** Steps 1-4 complete (Memory Window, RIS, Stress Simulation, RC Attestation)
**Estimate:** 2-3 hours implementation

---

## Mission

Instrument RC validation system with **Prometheus metrics** and **Grafana dashboards** to enable real-time observability of memory stability, RIS trends, and stress recovery patterns.

---

## Design Principles

1. **Metrics-first:** Export all RC validation signals to Prometheus
2. **Alerting-ready:** Define thresholds for automated alerts
3. **Trend analysis:** Support 7-day, 30-day, 90-day views
4. **No SSH debugging:** All diagnostics via dashboards + logs
5. **Low-overhead:** Metrics collection <1ms per evaluation

---

## Architecture

```
┌────────────────────────────────────────────────────┐
│           Governance Engine Evaluation             │
└───────────────────┬────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Memory Resonance    │
         │  Window              │
         │  - stability: 0.85   │
         │  - samples: 168      │
         │  - trend_24h: +0.02  │
         └──────────┬───────────┘
                    │
                    ├─────► record_memory_resonance(stats)
                    │       nova_memory_stability{} 0.85
                    │       nova_memory_samples{} 168
                    │       nova_memory_volatility{} 0.05
                    │
                    ▼
         ┌──────────────────────┐
         │  RIS Calculator      │
         │  - trsi: 0.88        │
         │  - ethics: 1.0       │
         │  - ris: 0.90         │
         └──────────┬───────────┘
                    │
                    ├─────► record_ris(ris_score, components)
                    │       nova_ris_score{} 0.90
                    │       nova_ris_component{type="memory"} 0.85
                    │       nova_ris_component{type="ethics"} 1.0
                    │
                    ▼
         ┌──────────────────────┐
         │  Stress Simulator    │
         │  - recovery: 0.95    │
         │  - baseline: 0.88    │
         └──────────┬───────────┘
                    │
                    └─────► record_stress_recovery(metrics)
                            nova_stress_recovery_rate{} 0.95
                            nova_stress_baseline_ris{} 0.88
                            nova_stress_ticks_to_recover{} 12


         ┌──────────────────────────────────┐
         │  Prometheus /metrics endpoint    │
         │  - Scraped every 15s             │
         │  - Retention: 90 days            │
         └────────────┬─────────────────────┘
                      │
                      ▼
         ┌──────────────────────────────────┐
         │  Grafana Dashboard               │
         │  - Memory Stability (7d trend)   │
         │  - RIS Score (hourly)            │
         │  - RC Criteria Gates (gauge)     │
         │  - Stress Recovery History       │
         │  - TRSI Distribution (histogram) │
         └──────────────────────────────────┘
```

---

## Component 1: Prometheus Metrics

### New Metrics

#### Memory Resonance Metrics

```python
# orchestrator/prometheus_metrics.py additions

# Memory stability gauge (7-day mean - stdev)
memory_stability_gauge = _get_or_register_gauge(
    "nova_memory_stability",
    "7-day rolling TRSI stability score (mean - volatility)",
)

# Memory sample count (track data sufficiency)
memory_samples_gauge = _get_or_register_gauge(
    "nova_memory_samples",
    "Number of TRSI samples in rolling window",
)

# Memory volatility (standard deviation)
memory_volatility_gauge = _get_or_register_gauge(
    "nova_memory_volatility",
    "7-day TRSI volatility (standard deviation)",
)

# 24-hour trend
memory_trend_gauge = _get_or_register_gauge(
    "nova_memory_trend_24h",
    "TRSI trend over last 24 hours",
)
```

#### RIS Component Metrics

```python
# Composite RIS score
ris_score_gauge = _get_or_register_gauge(
    "nova_ris_score",
    "Resonance Integrity Score: sqrt(memory_stability × ethics)",
)

# Individual RIS components (labeled)
ris_component_gauge = _get_or_register_gauge(
    "nova_ris_component",
    "Individual RIS component scores",
    labelnames=["component_type"]
)
# Labels: component_type={memory_stability, ethics_compliance}
```

#### Stress Simulation Metrics

```python
# Recovery rate from last stress test
stress_recovery_gauge = _get_or_register_gauge(
    "nova_stress_recovery_rate",
    "Recovery rate from last stress simulation",
)

# Baseline RIS before stress
stress_baseline_gauge = _get_or_register_gauge(
    "nova_stress_baseline_ris",
    "Baseline RIS before stress injection",
)

# Ticks to recover (latency)
stress_recovery_ticks_gauge = _get_or_register_gauge(
    "nova_stress_ticks_to_recover",
    "Number of ticks to recover to 90% baseline",
)

# Max deviation during stress
stress_max_deviation_gauge = _get_or_register_gauge(
    "nova_stress_max_deviation",
    "Maximum RIS deviation during stress test",
)

# Stress test timestamp (last run)
stress_last_run_gauge = _get_or_register_gauge(
    "nova_stress_last_run_timestamp",
    "Unix timestamp of last stress simulation",
)
```

#### RC Criteria Gate Metrics

```python
# Individual gate status (labeled)
rc_gate_status_gauge = _get_or_register_gauge(
    "nova_rc_gate_status",
    "RC criteria gate pass/fail status (1=pass, 0=fail)",
    labelnames=["gate_name"]
)
# Labels: gate_name={memory_stability, ris_score, stress_recovery, samples_sufficient}

# Overall RC pass
rc_overall_pass_gauge = _get_or_register_gauge(
    "nova_rc_overall_pass",
    "Overall RC criteria pass status (1=pass, 0=fail)",
)
```

### Recording Functions

```python
# orchestrator/prometheus_metrics.py

def record_memory_resonance(stats: dict) -> None:
    """Record memory resonance window statistics."""
    if not PROMETHEUS_ENABLED:
        return

    memory_stability_gauge.set(_clamp_unit(stats.get("stability", 0.5)))
    memory_samples_gauge.set(stats.get("count", 0))
    memory_volatility_gauge.set(_clamp_unit(stats.get("stdev", 0.0)))
    memory_trend_gauge.set(stats.get("trend_24h", 0.0))


def record_ris(ris_score: float, memory_stability: float, ethics_score: float) -> None:
    """Record RIS composite and components."""
    if not PROMETHEUS_ENABLED:
        return

    ris_score_gauge.set(_clamp_unit(ris_score))
    ris_component_gauge.labels(component_type="memory_stability").set(_clamp_unit(memory_stability))
    ris_component_gauge.labels(component_type="ethics_compliance").set(_clamp_unit(ethics_score))


def record_stress_recovery(metrics: dict) -> None:
    """Record stress simulation results."""
    if not PROMETHEUS_ENABLED:
        return

    stress_recovery_gauge.set(_clamp_unit(metrics.get("recovery_rate", 0.0)))
    stress_baseline_gauge.set(_clamp_unit(metrics.get("baseline_ris", 0.0)))
    stress_recovery_ticks_gauge.set(metrics.get("recovery_time_hours", 0))
    stress_max_deviation_gauge.set(_clamp_unit(metrics.get("max_deviation", 0.0)))
    stress_last_run_gauge.set(metrics.get("timestamp", time.time()))


def record_rc_criteria(criteria: dict) -> None:
    """Record RC gate status."""
    if not PROMETHEUS_ENABLED:
        return

    # Individual gates
    rc_gate_status_gauge.labels(gate_name="memory_stability").set(
        1.0 if criteria.get("memory_stability_pass") else 0.0
    )
    rc_gate_status_gauge.labels(gate_name="ris_score").set(
        1.0 if criteria.get("ris_pass") else 0.0
    )
    rc_gate_status_gauge.labels(gate_name="stress_recovery").set(
        1.0 if criteria.get("stress_recovery_pass") else 0.0
    )
    rc_gate_status_gauge.labels(gate_name="samples_sufficient").set(
        1.0 if criteria.get("samples_sufficient") else 0.0
    )

    # Overall
    rc_overall_pass_gauge.set(1.0 if criteria.get("overall_pass") else 0.0)
```

### Integration Points

**Governance Engine:**
```python
# orchestrator/router/epistemic_router.py (or governance engine)

from orchestrator.prometheus_metrics import (
    record_memory_resonance,
    record_ris,
    record_rc_criteria
)

def evaluate(...):
    # ... existing evaluation logic ...

    # Record memory resonance after window update
    if hasattr(self, 'memory_window'):
        stats = self.memory_window.get_window_stats()
        record_memory_resonance(stats)

    # Record RIS after computation
    if ris_score is not None:
        record_ris(ris_score, memory_stability, ethics_score)

    # Record RC criteria evaluation
    if rc_criteria is not None:
        record_rc_criteria(rc_criteria)
```

**Stress Simulator:**
```python
# orchestrator/predictive/stress_simulation.py

from orchestrator.prometheus_metrics import record_stress_recovery

def run_stress_test(...):
    # ... simulation logic ...

    metrics = {
        "recovery_rate": recovery_rate,
        "baseline_ris": baseline_ris,
        "recovery_time_hours": recovery_tick,
        "max_deviation": max_dev,
        "timestamp": time.time()
    }

    record_stress_recovery(metrics)
    return metrics
```

---

## Component 2: Grafana Dashboard

### Dashboard JSON Structure

File: `ops/grafana/dashboards/phase-7-rc-monitoring.json`

**Dashboard Layout:**

```
┌─────────────────────────────────────────────────────────┐
│ Phase 7.0-RC Validation Dashboard                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Row 1: RC Criteria Gates                              │
│  ┌──────────┬──────────┬──────────┬──────────┐        │
│  │ Memory   │ RIS      │ Stress   │ Overall  │        │
│  │ ≥0.80    │ ≥0.75    │ ≥0.90    │ RC Pass  │        │
│  │ [0.85]   │ [0.90]   │ [0.95]   │ [PASS]   │        │
│  └──────────┴──────────┴──────────┴──────────┘        │
│                                                         │
│  Row 2: Time Series Trends                             │
│  ┌─────────────────────────┬─────────────────────────┐│
│  │ Memory Stability (7d)   │ RIS Score (24h)         ││
│  │ [Line chart]            │ [Line + threshold]      ││
│  └─────────────────────────┴─────────────────────────┘│
│                                                         │
│  Row 3: Stress Resilience                              │
│  ┌─────────────────────────┬─────────────────────────┐│
│  │ Recovery History        │ Recovery Time (ticks)   ││
│  │ [Bar chart]             │ [Time series]           ││
│  └─────────────────────────┴─────────────────────────┘│
│                                                         │
│  Row 4: Distribution Analysis                          │
│  ┌─────────────────────────┬─────────────────────────┐│
│  │ TRSI Distribution (7d)  │ RIS Component Breakdown ││
│  │ [Histogram]             │ [Stacked area]          ││
│  └─────────────────────────┴─────────────────────────┘│
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Panel Configurations

#### Panel 1: RC Criteria Gates (Stat Panels)

```json
{
  "title": "Memory Stability Gate",
  "type": "stat",
  "targets": [{
    "expr": "nova_memory_stability",
    "legendFormat": "Current"
  }],
  "thresholds": {
    "mode": "absolute",
    "steps": [
      {"value": 0, "color": "red"},
      {"value": 0.75, "color": "yellow"},
      {"value": 0.80, "color": "green"}
    ]
  },
  "fieldConfig": {
    "defaults": {
      "min": 0,
      "max": 1,
      "decimals": 3
    }
  }
}
```

#### Panel 2: Memory Stability Trend (Time Series)

```json
{
  "title": "Memory Stability (7-day rolling)",
  "type": "timeseries",
  "targets": [
    {
      "expr": "nova_memory_stability",
      "legendFormat": "Stability"
    },
    {
      "expr": "0.80",
      "legendFormat": "RC Threshold"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "min": 0,
      "max": 1,
      "thresholds": {
        "steps": [
          {"value": 0.80, "color": "green"}
        ]
      }
    }
  }
}
```

#### Panel 3: RIS Score with Components (Stacked Area)

```json
{
  "title": "RIS Component Breakdown",
  "type": "timeseries",
  "targets": [
    {
      "expr": "nova_ris_component{component_type=\"memory_stability\"}",
      "legendFormat": "Memory Stability"
    },
    {
      "expr": "nova_ris_component{component_type=\"ethics_compliance\"}",
      "legendFormat": "Ethics"
    },
    {
      "expr": "nova_ris_score",
      "legendFormat": "Composite RIS"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "custom": {
        "fillOpacity": 20,
        "lineWidth": 2
      }
    }
  }
}
```

#### Panel 4: Stress Recovery History (Bar Chart)

```json
{
  "title": "Stress Recovery Rate History",
  "type": "barchart",
  "targets": [{
    "expr": "nova_stress_recovery_rate",
    "legendFormat": "Recovery Rate"
  }],
  "thresholds": {
    "steps": [
      {"value": 0, "color": "red"},
      {"value": 0.85, "color": "yellow"},
      {"value": 0.90, "color": "green"}
    ]
  }
}
```

#### Panel 5: TRSI Distribution (Heatmap)

```json
{
  "title": "TRSI Distribution (7-day window)",
  "type": "heatmap",
  "targets": [{
    "expr": "histogram_quantile(0.5, rate(nova_memory_stability[7d]))",
    "legendFormat": "TRSI distribution"
  }],
  "dataFormat": "tsbuckets"
}
```

---

## Component 3: Alerting Rules

File: `ops/prometheus/alerts/phase-7-rc-alerts.yml`

```yaml
groups:
  - name: phase_7_rc_validation
    interval: 5m
    rules:
      # Memory stability alert
      - alert: MemoryStabilityBelowThreshold
        expr: nova_memory_stability < 0.75
        for: 1h
        labels:
          severity: warning
          phase: 7.0-rc
        annotations:
          summary: "Memory stability below RC threshold"
          description: "Memory stability {{ $value | humanize }} < 0.75 for 1h"

      # RIS score alert
      - alert: RISScoreBelowThreshold
        expr: nova_ris_score < 0.70
        for: 30m
        labels:
          severity: warning
          phase: 7.0-rc
        annotations:
          summary: "RIS score below RC threshold"
          description: "RIS {{ $value | humanize }} < 0.70 for 30m"

      # RC overall failure
      - alert: RCValidationFailure
        expr: nova_rc_overall_pass == 0
        for: 15m
        labels:
          severity: critical
          phase: 7.0-rc
        annotations:
          summary: "RC validation failing"
          description: "Overall RC criteria not met for 15m"

      # Stress recovery degradation
      - alert: StressRecoveryDegraded
        expr: nova_stress_recovery_rate < 0.85
        for: 5m
        labels:
          severity: warning
          phase: 7.0-rc
        annotations:
          summary: "Stress recovery rate degraded"
          description: "Recovery {{ $value | humanize }} < 0.85"

      # Memory sample insufficiency
      - alert: InsufficientMemorySamples
        expr: nova_memory_samples < 24
        for: 1h
        labels:
          severity: info
          phase: 7.0-rc
        annotations:
          summary: "Insufficient TRSI samples for validation"
          description: "Only {{ $value }} samples (need ≥24 for 1-day baseline)"
```

---

## Implementation Steps

### Step 1: Add Prometheus Metrics (30 min)

```python
# File: orchestrator/prometheus_metrics.py

# 1. Add gauge definitions (lines 50-100)
# 2. Add recording functions (lines 200-250)
# 3. Export in __all__
```

**Tests:**
```python
# File: tests/metrics/test_rc_prometheus_metrics.py

def test_record_memory_resonance():
    stats = {"stability": 0.85, "count": 168, "stdev": 0.05, "trend_24h": 0.02}
    record_memory_resonance(stats)
    # Assert gauge values match

def test_record_ris():
    record_ris(ris_score=0.90, memory_stability=0.85, ethics_score=1.0)
    # Assert composite + component gauges

def test_record_stress_recovery():
    metrics = {"recovery_rate": 0.95, "baseline_ris": 0.88, "recovery_time_hours": 12}
    record_stress_recovery(metrics)
    # Assert stress gauges

def test_record_rc_criteria():
    criteria = {
        "memory_stability_pass": True,
        "ris_pass": True,
        "stress_recovery_pass": True,
        "samples_sufficient": True,
        "overall_pass": True
    }
    record_rc_criteria(criteria)
    # Assert all gates = 1.0
```

### Step 2: Integrate Recording Calls (30 min)

**Memory Window Integration:**
```python
# File: orchestrator/predictive/memory_resonance.py

def add_sample(...):
    # ... existing logic ...

    # Record after window update
    from orchestrator.prometheus_metrics import record_memory_resonance
    stats = self.get_window_stats()
    record_memory_resonance(stats)
```

**RIS Integration:**
```python
# File: orchestrator/predictive/ris_calculator.py

def compute_ris(...):
    ris = ...  # existing computation

    from orchestrator.prometheus_metrics import record_ris
    record_ris(ris, memory_stability, ethics_score)

    return ris
```

**Stress Simulator Integration:**
```python
# File: orchestrator/predictive/stress_simulation.py

def measure_recovery(...):
    metrics = {...}  # existing measurement

    from orchestrator.prometheus_metrics import record_stress_recovery
    record_stress_recovery(metrics)

    return metrics
```

### Step 3: Create Grafana Dashboard (45 min)

```bash
# File: ops/grafana/dashboards/phase-7-rc-monitoring.json
# - 5 panels as designed above
# - Time range: Last 7 days (default)
# - Refresh: 30s
# - Variables: none (single-instance for now)
```

### Step 4: Add Alerting Rules (15 min)

```bash
# File: ops/prometheus/alerts/phase-7-rc-alerts.yml
# - 5 alert rules as defined above
# - Test with Prometheus rule validation
```

### Step 5: Documentation & Testing (30 min)

**Runbook:**
```markdown
# File: docs/runbooks/phase-7-rc-monitoring.md

## Dashboard Access
- URL: http://grafana.nova/d/phase-7-rc
- Credentials: ops team SSO

## Key Panels
1. RC Gates: Green = passing, Red = failing
2. Memory Stability: Should stay ≥0.80
3. RIS Score: Should stay ≥0.75

## Alert Response
- MemoryStabilityBelowThreshold: Check TRSI volatility, review recent changes
- RISScoreBelowThreshold: Check ethics compliance + memory stability
- RCValidationFailure: Investigate all gate failures
```

**Tests:**
```python
# Test Prometheus exports
pytest tests/metrics/test_rc_prometheus_metrics.py -v

# Verify dashboard JSON valid
jq . ops/grafana/dashboards/phase-7-rc-monitoring.json

# Validate alert rules
promtool check rules ops/prometheus/alerts/phase-7-rc-alerts.yml
```

---

## Success Criteria

| Criterion | Validation |
|-----------|------------|
| All metrics exported | `curl localhost:9090/metrics \| grep nova_` shows 13+ metrics |
| Dashboard renders | Access Grafana URL, all panels load |
| Alerts configured | Prometheus /alerts shows 5 rules |
| Tests pass | 12 new metrics tests passing |
| No performance impact | Metrics recording <1ms per call |

---

## Rollback

If metrics cause issues:

```python
# Disable Prometheus export
export NOVA_ENABLE_PROMETHEUS=false

# Revert metrics code
git revert <phase5-commit>
```

Metrics are **side-effects only** - disabling doesn't affect core logic.

---

## Next Steps

After Phase 5 completion:
- **Phase 6:** CI/CD integration (weekly RC validation workflow)
- **Phase 7:** Final RC review document + tag `v7.0-rc-complete`

---

**Estimate:** 2-3 hours
**Dependencies:** Phases 1-4 complete
**Risk:** Low (metrics are non-invasive)
