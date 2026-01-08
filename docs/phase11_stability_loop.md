# Phase 11 - ORP Stability Loop

## Overview

The Operational Regime Policy (ORP) completes Nova's continuity stability loop by converting continuity signals into operational regimes and enforcing amplitude modulation across input, processing, and output layers.

## Stability Loop Diagram

```mermaid
flowchart TD
    %% Continuity Signals (Inputs)
    MSE[Meta-Stability Engine<br/>variance, trend, drift]
    URF[Unified Risk Field<br/>composite_risk]
    CSI[Continuity Stability Index<br/>C score]

    %% ORP Core (with internal hysteresis)
    ORP[Operational Regime Policy<br/>classify_regime<br/><i>includes hysteresis logic</i>]
    LEDGER[(Regime Transition Ledger<br/>append-only JSONL)]

    %% Amplitude Layers
    GOVERNOR[Wisdom Governor<br/>η scaling]
    EMOTION[Emotional Matrix<br/>intensity constriction]
    SLOT09[Slot09 Distortion<br/>sensitivity scaling]

    %% System Outputs
    BEHAVIOR[System Behavior<br/>learning amplitude<br/>expressive amplitude<br/>perceptual amplitude]

    %% Signal Flow
    MSE -->|mse_instability| ORP
    URF -->|composite_risk| ORP
    CSI -->|stability_signal| ORP

    ORP -->|regime + duration_s| LEDGER
    LEDGER -->|regime history| ORP

    ORP -->|effective_regime| GOVERNOR
    ORP -->|effective_regime| EMOTION
    ORP -->|effective_regime| SLOT09

    GOVERNOR -->|η_scaled| BEHAVIOR
    EMOTION -->|intensity_scaled| BEHAVIOR
    SLOT09 -->|threshold_scaled| BEHAVIOR

    %% Feedback Loop
    BEHAVIOR -.->|stabilized signals| MSE
    BEHAVIOR -.->|stabilized risk| URF
    BEHAVIOR -.->|improved continuity| CSI

    %% Styling
    classDef signals fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    classDef core fill:#fff4e6,stroke:#ff9800,stroke-width:3px
    classDef amplitude fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    classDef output fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    classDef storage fill:#fce4ec,stroke:#e91e63,stroke-width:2px

    class MSE,URF,CSI signals
    class ORP core
    class GOVERNOR,EMOTION,SLOT09 amplitude
    class BEHAVIOR output
    class LEDGER storage
```

## Regime Classification

```mermaid
stateDiagram-v2
    [*] --> Normal

    Normal --> Heightened: MSE oscillating OR URF moderate
    Normal --> ControlledDegradation: MSE unstable OR URF high

    Heightened --> Normal: Signals stabilize (≥60s)
    Heightened --> ControlledDegradation: MSE unstable OR URF high (≥300s)
    Heightened --> Emergency: MSE critical OR URF very high

    ControlledDegradation --> Recovery: Continuity improving (≥600s)
    ControlledDegradation --> Emergency: MSE critical OR URF very high

    Emergency --> Recovery: Continuity improving (≥900s)

    Recovery --> Normal: C ≥ 0.85 AND duration ≥ 1800s
    Recovery --> ControlledDegradation: Continuity degrades again

    note right of Normal
        η: 1.0 (baseline)
        Emotion: 1.0 (full)
        Slot09: 1.0 (normal)
        Min: 60s
    end note

    note right of Heightened
        η: 0.90-0.95 (modest damp)
        Emotion: 0.85-0.95
        Slot09: 1.05-1.15 (less sensitive)
        Min: 300s (5min)
    end note

    note right of ControlledDegradation
        η: 0.75 (significant damp)
        Emotion: 0.70
        Slot09: 1.30 (reduced sensitivity)
        Min: 600s (10min)
    end note

    note right of Emergency
        η: 0.50 (severe damp)
        Emotion: 0.50
        Slot09: 1.50 (minimal sensitivity)
        Min: 900s (15min)
    end note

    note right of Recovery
        η: 0.25 (minimal adaptation)
        Emotion: 0.60 (gradual increase)
        Slot09: 1.20 (cautious)
        Min: 1800s (30min)
    end note
```

## Hysteresis Enforcement

```mermaid
flowchart LR
    subgraph "Hysteresis Check"
        PROPOSED[Proposed Regime]
        CURRENT[Current Regime<br/>from Ledger]

        CHECK1{Same<br/>Regime?}
        CHECK2{Duration ≥<br/>Minimum?}
        CHECK3{Oscillation<br/>Detected?}

        ALLOW[Allow Transition<br/>effective = proposed]
        BLOCK[Block Transition<br/>effective = current]
        WARN[Warn<br/>advisory only]
    end

    PROPOSED --> CHECK1
    CURRENT --> CHECK1

    CHECK1 -->|Yes| ALLOW
    CHECK1 -->|No| CHECK2

    CHECK2 -->|Yes| CHECK3
    CHECK2 -->|No| BLOCK

    CHECK3 -->|≥3 in 5min| WARN
    CHECK3 -->|<3| ALLOW
    WARN --> ALLOW

    ALLOW -->|Return| DECISION[HysteresisDecision<br/>allowed=true]
    BLOCK -->|Return| DECISION2[HysteresisDecision<br/>allowed=false]

    classDef check fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef result fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    classDef block fill:#ffcdd2,stroke:#c62828,stroke-width:2px

    class CHECK1,CHECK2,CHECK3 check
    class ALLOW,WARN result
    class BLOCK block
```

## Amplitude Scaling Detail

```mermaid
flowchart TD
    subgraph "Governor η Scaling"
        G1[Base η<br/>AdaptiveWisdomGovernor]
        G2[ORP Multiplier<br/>0.25 - 1.0]
        G3[Scaled η<br/>Clamped to eta_min/eta_max]
        G1 --> G2
        G2 --> G3
    end

    subgraph "Emotional Constriction"
        E1[Emotional Intensity<br/>abs score]
        E2[ORP Multiplier<br/>0.50 - 1.0]
        E3[Constricted Intensity<br/>Preserves valence/topology]
        E1 --> E2
        E2 --> E3
    end

    subgraph "Slot09 Sensitivity"
        S1[Base Thresholds<br/>IDS stability/drift]
        S2[ORP Multiplier<br/>1.0 - 1.50]
        S3[Scaled Thresholds<br/>Higher = less sensitive]
        S1 --> S2
        S2 --> S3
    end

    ORP_REGIME[ORP Effective Regime] --> G2
    ORP_REGIME --> E2
    ORP_REGIME --> S2

    G3 -.->|Reduced learning<br/>during instability| STABLE[System Stability]
    E3 -.->|Reduced expression<br/>during instability| STABLE
    S3 -.->|Reduced false positives<br/>during instability| STABLE

    classDef input fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef transform fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef output fill:#f1f8e9,stroke:#558b2f,stroke-width:2px
    classDef stable fill:#e0f2f1,stroke:#00796b,stroke-width:3px

    class G1,E1,S1 input
    class G2,E2,S2 transform
    class G3,E3,S3 output
    class STABLE stable
```

## Key Properties

### Temporal Invariants
- **Minimum Durations**: Enforced per regime (60s - 1800s)
- **Oscillation Detection**: ≥3 transitions in 5min window (advisory)
- **Recovery Threshold**: Requires C ≥ 0.85 to exit recovery

### Amplitude Invariants
- **Multiplicative Scaling**: `output = input * multiplier` (not additive)
- **Bounded**: All multipliers in [0.0, 2.0] range
- **Topology Preserving**: What is detected/emitted unchanged, only magnitude affected

### Stability Invariants
- **No Uncontrolled Acceleration**: η damped during instability
- **No Noise Amplification**: Sensitivity reduced during instability
- **No Destructive Oscillation**: Hysteresis enforces minimum durations
- **No Abrupt Reversals**: Recovery ramping with C threshold
- **No Continuity Collapse**: Regime transitions deliberate, not reactive

## Feature Flags

All Phase 11 features are flag-gated (default off):

```bash
NOVA_ENABLE_REGIME_LEDGER=0        # Regime transition recording
NOVA_ENABLE_ETA_SCALING=0          # Governor η scaling
NOVA_ENABLE_EMOTIONAL_CONSTRICTION=0   # Emotion intensity scaling
NOVA_ENABLE_SLOT09_SENSITIVITY=0   # Slot09 threshold scaling
NOVA_ENABLE_ORP_HYSTERESIS=0       # Hysteresis enforcement (future)
```

## Observability

### Prometheus Metrics
- `nova_orp_current_regime` - Current regime (0-4 enum)
- `nova_orp_regime_duration_s` - Time in current regime
- `nova_orp_hysteresis_active` - 1 if blocking transitions
- `nova_orp_hysteresis_time_remaining_s` - Time until minimum duration met
- `nova_orp_oscillation_count` - Transitions in window
- `nova_orp_oscillation_detected` - 1 if oscillating
- `nova_orp_transitions_blocked_total` - Counter
- `nova_orp_transitions_allowed_total` - Counter

### Ledger
- Location: `src/nova/continuity/regime_transitions.jsonl`
- Format: Append-only JSONL (one regime entry per line)
- Schema: `contracts/regime@1.yaml`

## Test Coverage

- **Unit Tests**: 121 tests across 4 adapter modules
- **Integration Tests**: 49 tests across 3 integration points
- **Total**: 170 tests (100% coverage of ORP functionality)

## Contracts

- `contracts/orp_policy@1.yaml` - Regime classification rules
- `contracts/orp_stabilization@1.yaml` - Hysteresis enforcement
- `contracts/regime@1.yaml` - Regime data structure
- `contracts/hysteresis_decision@1.yaml` - Hysteresis decision structure
- `contracts/regime_transition_ledger@1.yaml` - Ledger schema

## References

- **Implementation**: `src/nova/continuity/{orp_policy,eta_scaling,emotional_posture,slot09_sensitivity,orp_hysteresis}.py`
- **Integration**: `src/nova/governor/adaptive_wisdom.py`, `src/nova/slots/slot03_emotional_matrix/emotional_matrix_engine.py`, `src/nova/slots/slot09_distortion_protection/hybrid_api.py`
- **Ontology**: `specs/nova_framework_ontology.v1.yaml` v1.5.0 (Phase 11 entry)
