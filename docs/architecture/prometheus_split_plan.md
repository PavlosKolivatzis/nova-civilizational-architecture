# Prometheus Metrics Split Plan

## Goal
Expose a public, low-noise metric stream for operational dashboards while retaining an internal slot-level feed for debugging, without double-counting or overloading `/metrics`.

## Architecture
| Component | Purpose |
|-----------|---------|
| `_INTERNAL_REGISTRY` | Full slot-level metrics, TRI diagnostics, counters, and heavy histograms |
| `_PUBLIC_REGISTRY` | Sanitized build/flag/system metrics safe for dashboards and third-party scrapers |
| `/metrics` | Serves `_PUBLIC_REGISTRY` + federation registry |
| `/metrics/internal` | Serves `_INTERNAL_REGISTRY` + federation registry |

## Namespacing & Labels
- All TRI/Slot metrics use `nova_tri_*`, `nova_slot07_*`, etc.
- Common label set: `slot`, `mode`, `source`.
  - TRI signals: `slot="04"`, `mode="canonized"`, `source="tri_truth_signal"`
  - Slot07 gates: `slot="07"`, `mode="governor"`, `source="tri_truth_signal"`
  - Slot01 attestation: `slot="01"`, `mode="root|legacy"`, `source="tri_truth_signal"`

## Exposure Policy
| Metric Type | Public | Internal |
|-------------|--------|----------|
| Build info, feature flags, root-mode flag | ✅ | ✅ |
| System pressure, LightClock, belief propagation | ✅ | ✅ |
| TRI canonization payloads (`nova_tri_coherence_current`, hashes) | ✅ (aggregate) | ✅ (full) |
| Slot07 drift/jitter/coherence | ✅ (current snapshot) | ✅ (full) |
| Slot01 attestation latency/events | ✅ (aggregate) | ✅ (full) |
| Slot-specific histograms, high-cardinality data | ❌ | ✅ |

## Operational Notes
1. `/metrics/internal` gated by `NOVA_ENABLE_PROMETHEUS`; use only for internal Grafana.
2. Federation registry appended to both responses to keep cross-node observability consistent.
3. Phase 10 metrics update runs before both endpoints to keep data synchronized.
4. CI smoke tests validate both endpoints (see `tests/web/test_prometheus_flags.py`).
