# Phase-3 Migration Plan — TRI Canonicalization & Threshold Integration

## 1. Canonical TRI → Slot01 Attestation Chain

Slot04 emits `tri_truth_signal@1` including:

- tri_coherence
- tri_drift_z
- tri_jitter
- canonical_hash

Slot01 Root-Mode registers:

- anchor_id ← canonical_hash
- metadata ← TRI payload

Semantic Mirror key:

- slot04.tri_truth_signal

## 2. Threshold-Driven Backpressure (Slot07)

Slot07 uses Threshold Manager:

- slot07_tri_drift_threshold
- slot07_stability_threshold_tri

Behavior:

- drift_z > threshold → reduce jobs
- stability < threshold → freeze mode

Prometheus exposes:

- nova_threshold_slot07_tri_drift
- nova_threshold_slot07_stability_tri

## 3. Slot06 Cultural Synthesis Integration

Slot06 uses tri_truth_signal for:

- principle preservation
- cultural risk calculation
- downstream contract emission

## 4. Slot10 Gatekeeper (Future-Proof)

LightClockGatekeeper now uses:

- `mirror.get_context("slot04.tri_belief")`
- threshold overrides from Threshold Manager
- deployment_gate decision is deterministic & observable
- drift/jitter/coherence thresholds (`tri_min_coherence`, `slot07_tri_drift_threshold`, `tri_max_jitter`)
- publishes structured gate results (reasons + thresholds) for downstream controllers

## 5. Observability Split (Public + Internal)

Public metrics: stable, user-facing  
Internal metrics: TRI, Slot03/06/07, attestation flows

## 6. Compatibility & Rollback

- `NOVA_SLOT01_ROOT_MODE=0` restores pre-Phase-2 behavior
- Internal registry disabled via `NOVA_DISABLE_INTERNAL_METRICS=1`
- No breaking API changes
