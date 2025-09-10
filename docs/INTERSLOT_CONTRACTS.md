# Inter-Slot Contracts

## Overview

This document defines the formal contracts between NOVA slots, specifying payload structures, data types, invariants, timeouts, retry policies, and fallback behaviors. All contracts follow versioned specifications with semantic compatibility guarantees.

## Contract Specifications

### EMOTION_REPORT@1

**Producer**: Slot 3 (Emotional Matrix)  
**Consumers**: Slot 6 (Cultural Synthesis)

```yaml
contract:
  id: EMOTION_REPORT@1
  version: "1"
  schema_version: "1.0.0"
  producer: slot03_emotional_matrix
  consumers: ["slot06_cultural_synthesis"]
  
payload:
  type: object
  required_fields:
    - emotional_tone
    - confidence
    - timestamp
  optional_fields:
    - cultural_impact
    - synthesis_weight
    - escalation_level
  
schema:
  emotional_tone:
    type: string
    enum: ["positive", "negative", "neutral", "complex", "ambiguous"]
    description: "Primary emotional assessment result"
  
  confidence:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "Confidence in emotional analysis (0.0 = uncertain, 1.0 = certain)"
  
  cultural_impact:
    type: number
    minimum: -1.0
    maximum: 1.0
    description: "Cultural sensitivity impact score"
    default: 0.0
  
  synthesis_weight:
    type: number
    minimum: 0.0
    maximum: 2.0
    description: "Weight for cultural synthesis processing"
    default: 1.0
  
  escalation_level:
    type: string
    enum: ["low", "medium", "high", "critical"]
    description: "Threat escalation level from emotional analysis"
  
  timestamp:
    type: number
    description: "Unix timestamp of analysis"

timeout:
  processing: 5000  # 5 seconds
  retry_backoff: [1000, 2000, 4000]  # exponential backoff in ms
  max_retries: 3

invariants:
  - "confidence must be inversely related to escalation_level for safety"
  - "cultural_impact must be bounded within [-1.0, 1.0]"
  - "timestamp must be within last 60 seconds for real-time processing"

fallback:
  type: NullAdapter
  safe_defaults:
    emotional_tone: "neutral"
    confidence: 0.5
    cultural_impact: 0.0
    synthesis_weight: 1.0
    escalation_level: "low"
```

### DELTA_THREAT@1

**Producer**: Slot 3 (Emotional Matrix)  
**Consumer**: Slot 2 (ΔTHRESH)

```yaml
contract:
  id: DELTA_THREAT@1
  version: "1"
  schema_version: "1.0.0"
  producer: slot03_emotional_matrix
  consumers: ["slot02_deltathresh"]

payload:
  type: object
  required_fields:
    - threat_level
    - confidence
    - timestamp
  optional_fields:
    - escalation_path
    - threat_vector
    - mitigation_suggestion

schema:
  threat_level:
    type: string
    enum: ["minimal", "low", "medium", "high", "critical", "existential"]
    description: "Assessed threat level from emotional analysis"
  
  escalation_path:
    type: array
    items:
      type: string
      enum: ["slot02_deltathresh", "slot04_tri", "slot07_production", "slot09_distortion"]
    description: "Recommended escalation path for threat handling"
  
  confidence:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "Confidence in threat assessment"
  
  threat_vector:
    type: string
    enum: ["content", "behavioral", "systematic", "emergent"]
    description: "Classification of threat vector"
  
  mitigation_suggestion:
    type: string
    maxLength: 500
    description: "Suggested mitigation approach"
  
  timestamp:
    type: number
    description: "Unix timestamp of threat detection"

timeout:
  processing: 3000  # 3 seconds - critical path
  retry_backoff: [500, 1000, 2000]
  max_retries: 2  # fewer retries for critical path

invariants:
  - "critical/existential threat_level must have confidence >= 0.8"
  - "escalation_path must include slot07_production for high+ threats"
  - "timestamp must be within last 30 seconds for threat relevance"

fallback:
  type: NullAdapter
  safe_defaults:
    threat_level: "minimal"
    confidence: 0.0
    escalation_path: []
    threat_vector: "content"
```

### TRI_REPORT@1

**Producer**: Slot 3 (Emotional Matrix)  
**Consumer**: Slot 4 (TRI Engine)

```yaml
contract:
  id: TRI_REPORT@1
  version: "1"
  schema_version: "1.0.0"
  producer: slot03_emotional_matrix
  consumers: ["slot04_tri_engine"]

payload:
  type: object
  required_fields:
    - risk_factors
    - emotional_state
    - timestamp
  optional_fields:
    - assessment
    - confidence_intervals
    - kalman_inputs

schema:
  risk_factors:
    type: array
    items:
      type: object
      properties:
        factor:
          type: string
          enum: ["emotional_instability", "content_risk", "behavioral_anomaly", "systemic_risk"]
        weight:
          type: number
          minimum: 0.0
          maximum: 1.0
        confidence:
          type: number
          minimum: 0.0
          maximum: 1.0
    minItems: 1
    maxItems: 10
  
  emotional_state:
    type: object
    required: ["primary", "intensity"]
    properties:
      primary:
        type: string
        enum: ["stable", "volatile", "escalating", "de-escalating"]
      intensity:
        type: number
        minimum: 0.0
        maximum: 1.0
      secondary_emotions:
        type: array
        items:
          type: string
  
  assessment:
    type: object
    properties:
      overall_risk:
        type: number
        minimum: 0.0
        maximum: 1.0
      recommendation:
        type: string
        enum: ["proceed", "caution", "escalate", "abort"]
      reasoning:
        type: string
        maxLength: 1000
  
  confidence_intervals:
    type: object
    properties:
      lower_bound:
        type: number
        minimum: 0.0
        maximum: 1.0
      upper_bound:
        type: number
        minimum: 0.0
        maximum: 1.0
      confidence_level:
        type: number
        enum: [0.90, 0.95, 0.99]
  
  kalman_inputs:
    type: object
    description: "Kalman filter inputs for TRI Engine Bayesian processing"
    properties:
      measurement:
        type: number
      uncertainty:
        type: number
      process_noise:
        type: number
  
  timestamp:
    type: number
    description: "Unix timestamp of assessment"

timeout:
  processing: 8000  # 8 seconds for complex TRI analysis
  retry_backoff: [2000, 4000, 8000]
  max_retries: 3

invariants:
  - "risk_factors array must have at least one factor with weight > 0.5"
  - "emotional_state.intensity must correlate with overall_risk"
  - "confidence_intervals.upper_bound >= confidence_intervals.lower_bound"

fallback:
  type: NullAdapter
  safe_defaults:
    risk_factors: []
    emotional_state:
      primary: "stable"
      intensity: 0.1
    assessment:
      overall_risk: 0.1
      recommendation: "proceed"
```

### PRODUCTION_CONTROL@1

**Producer**: Slot 3 (Emotional Matrix)  
**Consumer**: Slot 7 (Production Controls)

```yaml
contract:
  id: PRODUCTION_CONTROL@1
  version: "1"
  schema_version: "1.0.0"
  producer: slot03_emotional_matrix
  consumers: ["slot07_production_controls"]

payload:
  type: object
  required_fields:
    - control_action
    - severity
    - timestamp
  optional_fields:
    - timeout
    - reason
    - recovery_suggestion

schema:
  control_action:
    type: string
    enum: ["continue", "throttle", "pause", "circuit_break", "emergency_stop"]
    description: "Required production control action"
  
  severity:
    type: string
    enum: ["info", "warning", "error", "critical", "fatal"]
    description: "Severity level of the control requirement"
  
  timeout:
    type: number
    minimum: 1000
    maximum: 300000  # 5 minutes max
    description: "Timeout in milliseconds for control action"
    default: 30000
  
  reason:
    type: string
    maxLength: 200
    description: "Human-readable reason for control action"
  
  recovery_suggestion:
    type: string
    maxLength: 500
    description: "Suggested recovery procedure"
  
  timestamp:
    type: number
    description: "Unix timestamp of control decision"

timeout:
  processing: 1000  # 1 second - critical control path
  retry_backoff: [200, 500, 1000]
  max_retries: 2

invariants:
  - "emergency_stop must have severity >= 'critical'"
  - "circuit_break must have timeout <= 60000ms"
  - "timestamp must be within last 10 seconds for control relevance"

fallback:
  type: CircuitBreaker
  safe_defaults:
    control_action: "pause"  # safe default action
    severity: "warning"
    timeout: 30000
    reason: "Emotional matrix unavailable - applying safe defaults"
```

### CULTURAL_PROFILE@1

**Producer**: Slot 6 (Cultural Synthesis)  
**Consumers**: Slot 2 (ΔTHRESH), Slot 4 (TRI Engine), Slot 10 (Deployment)

```yaml
contract:
  id: CULTURAL_PROFILE@1
  version: "1"
  schema_version: "1.0.0"
  producer: slot06_cultural_synthesis
  consumers: ["slot02_deltathresh", "slot04_tri_engine", "slot10_deployment"]

payload:
  type: object
  required_fields:
    - cultural_weights
    - synthesis_result
    - timestamp
  optional_fields:
    - confidence
    - regional_factors
    - deployment_constraints
    - risk_cultural_factors

schema:
  cultural_weights:
    type: object
    description: "Cultural dimension weights for processing"
    patternProperties:
      "^[a-zA-Z_]+$":
        type: number
        minimum: 0.0
        maximum: 1.0
    examples:
      individualism: 0.7
      collectivism: 0.3
      power_distance: 0.4
      uncertainty_avoidance: 0.6
  
  synthesis_result:
    type: object
    required: ["overall_cultural_fit", "recommendation"]
    properties:
      overall_cultural_fit:
        type: number
        minimum: 0.0
        maximum: 1.0
      recommendation:
        type: string
        enum: ["proceed", "adapt", "localize", "defer"]
      adaptation_needed:
        type: array
        items:
          type: string
      confidence_score:
        type: number
        minimum: 0.0
        maximum: 1.0
  
  confidence:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "Overall confidence in cultural analysis"
    default: 0.8
  
  regional_factors:
    type: array
    items:
      type: object
      properties:
        region:
          type: string
        impact_score:
          type: number
          minimum: -1.0
          maximum: 1.0
        considerations:
          type: array
          items:
            type: string
  
  deployment_constraints:
    type: object
    description: "Constraints for Slot 10 deployment"
    properties:
      rollout_strategy:
        type: string
        enum: ["global", "regional", "gradual", "restricted"]
      cultural_gates:
        type: array
        items:
          type: string
      risk_mitigation:
        type: array
        items:
          type: string
  
  risk_cultural_factors:
    type: array
    description: "Cultural risk factors for TRI Engine"
    items:
      type: object
      properties:
        factor:
          type: string
        risk_level:
          type: number
          minimum: 0.0
          maximum: 1.0
        mitigation:
          type: string
  
  timestamp:
    type: number
    description: "Unix timestamp of cultural analysis"

timeout:
  processing: 10000  # 10 seconds for complex cultural analysis
  retry_backoff: [2000, 5000, 10000]
  max_retries: 3

invariants:
  - "cultural_weights values must sum to <= 2.0 for normalization"
  - "synthesis_result.overall_cultural_fit must align with recommendation"
  - "high risk_cultural_factors must have corresponding mitigation"

fallback:
  type: NullAdapter
  safe_defaults:
    cultural_weights:
      default: 0.5
    synthesis_result:
      overall_cultural_fit: 0.5
      recommendation: "defer"
      confidence_score: 0.1
    confidence: 0.1
    deployment_constraints:
      rollout_strategy: "restricted"
```

## Contract Evolution & Compatibility

### Versioning Strategy

1. **Major Version Changes** (`EMOTION_REPORT@2`): Breaking schema changes, incompatible payloads
2. **Minor Version Changes** (`EMOTION_REPORT@1.1`): Additive changes, backward compatible
3. **Patch Version Changes** (`EMOTION_REPORT@1.0.1`): Documentation, validation improvements

### Compatibility Matrix

| Producer Version | Consumer Version | Compatibility | Notes |
|------------------|------------------|---------------|-------|
| 1.0 | 1.0 | ✅ Full | Exact match |
| 1.1 | 1.0 | ✅ Backward | New fields ignored |
| 1.0 | 1.1 | ⚠️ Forward | Missing fields use defaults |
| 2.0 | 1.x | ❌ Incompatible | Breaking changes |

### Schema Governance

- **Contract Freeze**: Changes require PR labels (`CONTRACT:BUMP`, `CONTRACT:EXPLAIN`)
- **Validation**: CI workflows validate all contracts against sample payloads
- **Drift Detection**: Nightly validation ensures schema compliance
- **CODEOWNERS**: All schema changes require architectural review

## Implementation Guidelines

### Error Handling

```python
def handle_contract_failure(contract_id: str, error: Exception) -> dict:
    """Standard error handling for contract failures."""
    fallback = get_fallback_adapter(contract_id)
    log_contract_failure(contract_id, error)
    return fallback.get_safe_defaults()
```

### Timeout Management

```python
async def send_with_timeout(contract_id: str, payload: dict) -> dict:
    """Send contract payload with proper timeout handling."""
    config = get_contract_config(contract_id)
    
    for attempt in range(config.max_retries + 1):
        try:
            return await asyncio.wait_for(
                send_payload(payload), 
                timeout=config.processing_timeout / 1000
            )
        except asyncio.TimeoutError:
            if attempt < config.max_retries:
                await asyncio.sleep(config.retry_backoff[attempt] / 1000)
                continue
            return get_fallback_response(contract_id)
```

### NullAdapter Implementation

```python
class EmotionReportNullAdapter:
    """Safe fallback for EMOTION_REPORT@1 contract."""
    
    def get_safe_defaults(self) -> dict:
        return {
            "emotional_tone": "neutral",
            "confidence": 0.5,
            "cultural_impact": 0.0,
            "synthesis_weight": 1.0,
            "escalation_level": "low",
            "timestamp": time.time()
        }
    
    def validate_invariants(self, payload: dict) -> bool:
        """Validate contract invariants."""
        return (
            0.0 <= payload.get("confidence", 0) <= 1.0 and
            -1.0 <= payload.get("cultural_impact", 0) <= 1.0 and
            payload.get("timestamp", 0) > time.time() - 60
        )
```

## Monitoring & Observability

### Contract Metrics

- **Success Rate**: Percentage of successful contract invocations
- **Latency Distribution**: P50, P95, P99 latency for each contract
- **Fallback Rate**: Percentage of requests using NullAdapter fallbacks
- **Error Types**: Classification of contract failures
- **Timeout Rate**: Percentage of requests timing out

### Health Checks

Each contract includes health validation:

```yaml
health_check:
  endpoint: "/health/contracts/{contract_id}"
  validation:
    - schema_compliance
    - invariant_validation
    - performance_bounds
    - fallback_availability
  frequency: "30s"
  alerts:
    fallback_rate: "> 5%"
    error_rate: "> 1%"
    latency_p99: "> 10s"
```

## Security Considerations

### Data Protection

- **Sensitive Fields**: Mark fields containing PII or sensitive cultural data
- **Access Controls**: Role-based access for contract modification
- **Audit Trail**: Log all contract invocations for compliance
- **Encryption**: Consider encryption for sensitive inter-slot communication

### Rate Limiting

- **Per-Contract Limits**: Individual rate limits for each contract type
- **Burst Protection**: Allow temporary bursts with longer-term rate limiting
- **Priority Queuing**: Prioritize critical contracts (PRODUCTION_CONTROL@1)

### Validation

- **Input Sanitization**: Validate all payload fields against schema
- **Invariant Checking**: Enforce business rule invariants
- **Size Limits**: Prevent oversized payloads from consuming resources
- **Type Safety**: Strong typing for all contract interfaces