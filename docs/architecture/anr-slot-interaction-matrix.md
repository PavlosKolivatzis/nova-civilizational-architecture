# ANR Architecture & Slot Interaction Matrix

## Overview

The Adaptive Neural Router (ANR) serves as Nova's cognitive orchestration layer, dynamically routing requests through optimal slot combinations based on contextual features and learned outcomes. This document provides a comprehensive view of how ANR coordinates all 12 Nova slots for civilizational-scale intelligence.

## ANR Core Architecture

### Router Engine
- **Type**: LinUCB Contextual Bandit with ε-greedy exploration
- **Mode**: Shadow learning with progressive live deployment (10% pilot → 100%)
- **Features**: 11-dimensional contextual vector from slot signals
- **Learning**: Immediate feedback (latency + TRI) + deployment feedback (SLO compliance)

### Route Definitions

| Route | Description | Slot Pattern | Use Case |
|-------|-------------|--------------|----------|
| **R1** | Standard | Slot4 → Slot5 → Slot6 → Slot10 | Balanced coordination |
| **R2** | Strict | Slot4(strict) → Slot6(conservative) → Slot10 | High-safety scenarios |
| **R3** | Fast | Slot4 → Slot6(light) → Slot10 | Performance-optimized |
| **R4** | Block | None (guardrail) | Safety fallback |
| **R5** | Feedback-Heavy | Slot4(strict) → Slot6 → Slot7(backpressure) → Slot10 | Learning-focused |

### Safety Mechanisms
- **Kill Switch**: `NOVA_ANR_KILL=1` forces R4 guardrail
- **Fast Cap**: R3 ≤ 15% probability under anomalies
- **Pilot Gate**: Gradual rollout control via `NOVA_ANR_PILOT`
- **Anomaly Mask**: Conservative routing during stress conditions

## Slot Interaction Matrix

### Slot 01 - Truth Anchor
**Role**: Reality grounding and temporal consistency baseline
- **ANR Integration**: Provides truth coherence signals for route validation
- **Feature Contribution**: Baseline truth score for TRI delta calculation
- **Route Impact**: All routes except R4 validate against truth anchor
- **Dependencies**: Independent foundation layer

### Slot 02 - ΔTHRESH (Content Processing)
**Role**: Threshold management and risk screening with TRI scoring
- **ANR Integration**: Contributes system pressure and risk metrics to feature vector
- **Feature Contribution**: `system_pressure`, pattern detection signals
- **Route Impact**: R2/R5 (strict routes) require enhanced ΔTHRESH validation
- **Dependencies**: Consumes Slot4 TRI outputs, feeds Slot10 deployment

### Slot 03 - Emotional Matrix
**Role**: Emotional state analysis and safety screening
- **ANR Integration**: Provides emotional context and threat escalation signals
- **Feature Contribution**: `emotional_state`, threat level indicators
- **Route Impact**: Influences all routes via safety policy adjustments
- **Dependencies**: Independent analysis, coordinates with Slot7 for escalation

### Slot 04 - TRI Engine (Truth Resonance Index)
**Role**: Truth evaluation and quality assessment with drift detection
- **ANR Integration**: Core feature provider for routing decisions
- **Feature Contribution**: `tri_drift_z`, truth coherence, confidence levels
- **Route Impact**:
  - R1: Standard TRI evaluation
  - R2/R5: Strict TRI validation with enhanced safety
  - R3: Fast TRI evaluation with relaxed thresholds
- **Dependencies**: Consumes Slot1 truth anchor, feeds all downstream slots

### Slot 05 - Constellation Mapping
**Role**: Pattern discovery and relationship analysis
- **ANR Integration**: Provides contextual complexity metrics
- **Feature Contribution**: Pattern density, relationship coherence
- **Route Impact**:
  - R1: Full constellation analysis
  - R2: Conservative pattern validation
  - R3: Skipped for performance (fast path)
  - R5: Enhanced pattern correlation
- **Dependencies**: Coordinates with Slot6 for cultural synthesis

### Slot 06 - Cultural Synthesis
**Role**: Cultural adaptation and principle preservation
- **ANR Integration**: Provides cultural coherence and adaptation effectiveness
- **Feature Contribution**: `cultural_coherence`, `adaptation_rate`
- **Route Impact**:
  - R1: Normal cultural synthesis
  - R2: Conservative synthesis with enhanced safety
  - R3: Light synthesis for speed
  - R5: Full synthesis with feedback integration
- **Dependencies**: Consumes Slot5 patterns, coordinates with Slot10 deployment

### Slot 07 - Production Controls
**Role**: Circuit breaking, rate limiting, and system protection
- **ANR Integration**: Core safety coordinator and backpressure source
- **Feature Contribution**: `system_pressure`, circuit breaker state, resource protection
- **Route Impact**:
  - All routes: Safety constraint enforcement
  - R5: Explicit backpressure emission for learning
  - Emergency: Can force R4 guardrail routing
- **Dependencies**: Monitors all slots, coordinates with ANR safety systems

### Slot 08A - Memory Ethics
**Role**: Ethical boundaries and identity protection
- **ANR Integration**: Provides ethical constraint signals
- **Feature Contribution**: Ethics violation flags, identity protection status
- **Route Impact**: Can trigger safety masks forcing conservative routes
- **Dependencies**: IDS integration, coordinates with Slot7 for violations

### Slot 08B - Memory Lock (Processual 4.0)
**Role**: Cryptographic integrity and self-healing memory protection
- **ANR Integration**: Provides system integrity and anomaly detection
- **Feature Contribution**: `integrity_score`, tamper detection, quarantine status
- **Route Impact**: Integrity failures can force R2/R4 conservative routing
- **Dependencies**: Independent security layer, coordinates with all slots

### Slot 09 - Distortion Protection
**Role**: Reality verification and infrastructure-aware anomaly detection
- **ANR Integration**: Critical phase lock and coherence provider
- **Feature Contribution**: `phase_lock_strength`, `anomaly_engagement`, coherence level
- **Route Impact**:
  - High coherence: Can relax safety constraints
  - Low coherence: Forces conservative routing
  - Anomaly engaged: Triggers fast-cap and conservative masks
- **Dependencies**: Light-clock integration, IDS policy coordination

### Slot 10 - Civilizational Deployment
**Role**: Deployment orchestration with MLS audit and institutional profiling
- **ANR Integration**: Final execution layer and feedback source
- **Feature Contribution**: `deployment_health`, rollback rates, SLO compliance
- **Route Impact**: All routes (except R4) culminate in Slot10 deployment
- **Dependencies**: Consumes outputs from Slots 2,4,6; coordinates with cultural synthesis

## ANR Decision Process

### 1. Context Feature Extraction
```python
feature_vector = [
    tri_drift_z,           # Slot 04 - Truth coherence drift
    system_pressure,       # Slot 02/07 - System load indicators
    phase_jitter,          # Slot 09 - Phase lock stability
    cultural_coherence,    # Slot 06 - Cultural synthesis quality
    adaptation_rate,       # Slot 06 - Cultural adaptation speed
    confidence_level,      # Slot 04 - TRI confidence
    emotional_state,       # Slot 03 - Emotional analysis output
    integrity_score,       # Slot 08B - Memory integrity
    anomaly_engagement,    # Slot 09 - Distortion detection
    phase_lock_strength,   # Slot 09 - Light-clock coherence
    deployment_health      # Slot 10 - Deployment success rate
]
```

### 2. Safety Mask Application
- **Hard blocks**: Consent violations, memory ethics, ACL constraints
- **Anomaly coordination**: Phase 4.1 anomaly engagement forces conservative routing
- **Fast-cap enforcement**: R3 probability ceiling under stress conditions

### 3. Route Probability Calculation
- **LinUCB scoring**: Upper confidence bound for exploration-exploitation
- **ε-greedy policy**: Small exploration probability for route discovery
- **Safety normalization**: Probabilities adjusted for active constraints

### 4. Execution Plan Generation
Each route generates a specific execution plan:
- **Step sequencing**: Defined slot coordination patterns
- **Context passing**: Rich context propagation between slots
- **Safety validation**: Conservative flags and strict mode switches

### 5. Feedback Integration
- **Immediate feedback**: Latency and TRI delta for real-time learning
- **Deployment feedback**: SLO compliance and rollback detection
- **Reward normalization**: Balanced learning signals across routes

## Semantic Mirror Integration

ANR publishes decision context and feedback via semantic mirror keys:

| Key | Purpose | TTL | Consumer |
|-----|---------|-----|----------|
| `router.anr_shadow_decision` | Shadow mode decisions | 120s | Monitoring |
| `router.anr_live_decision` | Live traffic decisions | 120s | Operations |
| `router.current_decision_id` | Active decision correlation | 600s | Feedback loops |
| `router.anr_reward_immediate` | Real-time feedback | 600s | Learning |
| `router.anr_reward_deployment` | Deployment outcomes | 3600s | Analysis |

## Configuration Parameters

### Core ANR Settings
```bash
NOVA_ANR_ENABLED=1           # Enable adaptive routing
NOVA_ANR_PILOT=0.10          # Live traffic percentage
NOVA_ANR_EPSILON=0.05        # Exploration rate
NOVA_ANR_ALPHA=0.8           # LinUCB confidence
NOVA_ANR_RIDGE=0.01          # Regularization
```

### Safety Controls
```bash
NOVA_ANR_KILL=0                    # Emergency kill switch
NOVA_ANR_MAX_FAST_PROB=0.15        # Fast route cap
NOVA_ANR_STRICT_ON_ANOMALY=1       # Conservative under stress
NOVA_ANR_LEARN_SHADOW=1            # Enable shadow learning
```

### Integration Flags
```bash
NOVA_LIGHTCLOCK_DEEP=1             # Deep phase lock integration
NOVA_USE_SHARED_HASH=0             # Shared audit hash (disabled)
IDS_ENABLED=1                      # IDS policy integration
NOVA_ENABLE_PROMETHEUS=1           # Metrics export
```

## Production Deployment Strategy

### Phase 1: Shadow Learning (Complete)
- 100% shadow mode with full learning
- Route quality assessment via RSI (Route Selection Index)
- Safety mechanism validation

### Phase 2: Pilot Deployment (Current - 10%)
- 10% live traffic via ANR routing
- Comprehensive monitoring and alerting
- Instant rollback capability

### Phase 3: Progressive Rollout (Planned)
- 25% → 50% → 75% → 100% gradual increase
- Gate validation at each stage
- Continuous safety monitoring

### Phase 4: Full Production (Target)
- 100% adaptive routing (excluding anomaly conditions)
- Autonomous promotion/rollback based on metrics
- Continuous optimization and learning

## Monitoring & Observability

### Key Metrics
- **RSI (Route Selection Index)**: Shadow vs live agreement (target ≥ 0.85)
- **TRI Delta**: Truth coherence impact measurement
- **Rollback Rate**: Deployment stability per 1k decisions (target ≤ 0.1)
- **Live Rate**: Percentage using live vs shadow routing

### Health Endpoints
- `GET /health` - System health including ANR status
- `GET /router/stats` - ANR operational statistics
- `GET /metrics` - Prometheus metrics export
- `GET /semantic-mirror/keys` - Decision correlation tracking

### Emergency Procedures
```bash
# Immediate rollback
export NOVA_ANR_ENABLED=0

# Partial rollback
export NOVA_ANR_PILOT=0.05

# Safety mode
export NOVA_ANR_KILL=1
```

## Summary

The ANR represents Nova's evolution from static routing to adaptive neural intelligence, orchestrating all 12 slots with:

- **Contextual Intelligence**: 11-dimensional feature extraction from slot signals
- **Safety-First Design**: Multi-layer protection with instant rollback
- **Continuous Learning**: Real-time adaptation via contextual bandits
- **Production Readiness**: Comprehensive monitoring and operational procedures

ANR transforms Nova from a deterministic cognitive architecture into an adaptive intelligence system that learns optimal coordination patterns while maintaining absolute safety boundaries.