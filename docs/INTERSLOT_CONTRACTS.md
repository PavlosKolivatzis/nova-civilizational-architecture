```yaml
EMOTION_REPORT@1:
  version: 1
  producer: slot03_emotional_matrix
  fields:
    - emotional_tone: string
    - score: number
    - confidence: number
    - safety:
        is_safe: boolean
        violations: array
  timeout: 2s
  retry: exponential (3 tries, base 100ms)
  null_adapter: {emotional_tone: "neutral", score: 0.0, confidence: 0.0, safety: {is_safe: true}}
```

```yaml
DELTA_THREAT@1:
  version: 1
  consumer: slot02_deltathresh
  fields:
    - threat_level: string (low|medium|high|critical)
    - confidence: number
    - content_hash: string
  timeout: 1s
  backoff: jittered exponential (max 5s)
  safe_fallback: {action: "allow"}
```

```yaml
TRI_REPORT@1:
  version: 1
  consumer: slot04_tri_engine
  fields:
    - tri_score: number
    - variance: number
    - source_slot: string
  timeout: 1s
  retry: none
  null_adapter: {tri_score: 0.0, variance: 1.0, source_slot: "null"}
```

```yaml
PRODUCTION_CONTROL@1:
  version: 1
  consumer: slot07_production_controls
  fields:
    - action: string (allow|quarantine)
    - rate_limited: boolean
    - reason_codes: array
  timeout: 500ms
  retry: linear (2 attempts)
  null_adapter: {action: "allow", rate_limited: false, reason_codes: []}
```

```yaml
CULTURAL_PROFILE@1:
  version: 1
  producer: slot06_cultural_synthesis
  fields:
    - culture_id: string
    - principle_preservation_score: number
    - residual_risk: number
  timeout: 2s
  retry: none
  null_adapter: {culture_id: "default", principle_preservation_score: 0.5, residual_risk: 0.5}
```
