# Runbook: Blocked Deployment Remediation

## Problem
Slot 6 Cultural Synthesis is blocking content deployment with high residual risk or low principle preservation scores.

## Symptoms
- `/health/config` shows high `decisions.blocked` count
- Application logs show `BLOCKED_PRINCIPLE_VIOLATION` or `BLOCKED_CULTURAL_SENSITIVITY`
- Users report content not being approved for deployment

## Investigation Steps

### 1. Check Current Decision Metrics
```bash
curl /health/config | jq '.slot6'
```

Look for:
- `last_decision.residual_risk` > 0.7
- `last_decision.pps` < 0.3
- `decisions.blocked` trending upward

### 2. Examine Recent Decisions
```bash
# Check logs for decision details
grep "Cultural synthesis decision" /var/log/nova.log | tail -10

# Check for pattern in blocked content
grep "BLOCKED_PRINCIPLE_VIOLATION" /var/log/nova.log | head -5
```

### 3. Validate Input Quality
```bash
# Check Slot 2 TRI scores feeding into Slot 6
curl /health/tri | jq '.recent_scores'

# Verify layer scores are reasonable
curl /health/deltathresh | jq '.layer_analysis'
```

## Common Root Causes & Solutions

### High Residual Risk (>0.7)
**Cause**: Low TRI scores or high layer risks from Slot 2
```bash
# Solution: Check Slot 2 detection patterns
grep "TRI calculation" /var/log/nova.log | tail -5

# Verify content isn't genuinely high-risk
# If content is legitimate, consider TRI threshold adjustment
```

### Low Principle Preservation (<0.3)
**Cause**: Low anchor confidence or ideology push detected
```bash
# Solution: Check anchor confidence scores
curl /health/anchor | jq '.confidence_metrics'

# Verify cultural context is appropriate
curl /health/config | jq '.cultural_synthesis.institution_type'
```

### Consent Issues
**Cause**: Content requires consent but consent not provided
```bash
# Solution: Ensure consent flow is working
grep "consent_required" /var/log/nova.log | tail -5

# Check consent validation logic
curl /health/consent | jq '.validation_status'
```

## Emergency Procedures

### Temporary Bypass (Use with Caution)
```bash
# For critical deployments only - requires approval
export NOVA_EMERGENCY_BYPASS=1
export NOVA_BYPASS_REASON="Production incident #12345"

# Deploy with emergency bypass
./deploy.sh --emergency
```

### Threshold Adjustment
```bash
# Lower risk threshold temporarily (requires SRE approval)  
curl -X POST /admin/thresholds \
  -H "NOVA-API-KEY: $NOVA_API_KEY" \
  -d '{"residual_risk_threshold": 0.8}'
```

## Prevention

1. **Monitor trends**: Set alerts on blocked rate >15%
2. **Content quality**: Improve upstream content filtering  
3. **TRI calibration**: Regular review of TRI thresholds
4. **Cultural alignment**: Validate institution configuration

## Escalation

- **L1**: Operations team attempts standard remediation
- **L2**: Engineering reviews thresholds and decision logic
- **L3**: Architecture team evaluates cultural synthesis parameters

Contact: `#nova-operations` for immediate assistance