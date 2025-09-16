# Observability — Nova Processual System

## Overview

The Nova Civilizational Architecture provides comprehensive observability for all 10 Processual slots through multiple monitoring systems, metrics export, audit trails, and health checking.

## 📊 Health Monitoring

### Morning Health Pulse
Comprehensive system health check across all slots:

```bash
# Run complete health assessment
PYTHONPATH=. python orchestrator/health_pulse.py

# Expected output:
# Nova Civilizational Architecture - Morning Health Pulse
# Component Health Status:
#   Slot 8 Memory Lock & IDS: HEALTHY (MTTR <=5s)
#   Slot 4 TRI Engine: HEALTHY (O(1) rolling statistics)
#   Slot 10 Processual Deployment: HEALTHY (Progressive canary)
# SYSTEM STATUS: PROCESSUAL (4.0) - All slots operational
# Total test validation: 506 tests passing
```

### Individual Slot Health Checks
```bash
# Slot-specific health verification
pytest slots/slot08_memory_lock/tests/ -v    # 23 autonomy tests
pytest slots/slot04_tri/tests/ -v           # 7 autonomy tests
pytest slots/slot10_civilizational_deployment/tests/ -v  # 9 autonomy tests

# Full system validation
python -m pytest -q  # 506 total tests
```

## 🔍 Slot 10 Deployment Observability

### Prometheus Metrics Export

**Endpoint**: Produced by `CanaryMetricsExporter.get_prometheus_metrics()`

**Key Metrics**:
- `slot10_deploy_stage_pct` - Current canary deployment stage percentage
- `slot10_deploy_active` - Whether canary deployment is active (1=yes, 0=no)
- `slot10_gate_status` - Gate evaluation status (1=pass, 0=fail)
- `slot10_slo_violations` - Current stage SLO violation count
- `slot10_error_rate` - Current error rate
- `slot10_latency_p95_ms` - 95th percentile latency in milliseconds
- `slot10_rollback_triggered` - Whether rollback was triggered (1=yes, 0=no)

**Usage Example**:
```python
from slots.slot10_civilizational_deployment.core import CanaryMetricsExporter, CanaryController

# Initialize with metrics export
metrics_exporter = CanaryMetricsExporter(export_interval_s=30.0)
controller = CanaryController(policy, gatekeeper, health_feed, metrics_exporter=metrics_exporter)

# Export current metrics
current_metrics = metrics_exporter.capture_canary_state(controller)
prometheus_text = metrics_exporter.get_prometheus_metrics(current_metrics)

# Write to file for Prometheus collection
with open('/var/lib/node_exporter/textfile_collector/slot10.prom', 'w') as f:
    f.write(prometheus_text)
```

### Audit Trail

**Hash-chained HMAC-SHA256 records** provide tamper-evident operational history:

```python
from slots.slot10_civilizational_deployment.core import AuditLog

# Initialize audit logging (opt-in)
audit = AuditLog(log_dir=Path("audit_logs"))
controller = CanaryController(policy, gatekeeper, health_feed, audit=audit)

# Audit records are automatically created for:
# - Deployment start events
# - Stage promotions
# - Rollback triggers
# - Gate evaluation results
```

**Audit Record Format**:
```json
{
  "ts_ms": 1726502400000,
  "action": "promote",
  "stage_idx": 2,
  "reason": "Promoted to 25.0%",
  "pct_from": 5.0,
  "pct_to": 25.0,
  "metrics": {"stage_duration": 120.5},
  "prev": "abc123...",
  "hash": "def456...",
  "sig": "789xyz..."
}
```

**Verification**:
```python
# Verify audit chain integrity
audit_log = AuditLog(log_dir=Path("audit_logs"))
is_valid = audit_log.verify_file()  # Returns True if all signatures and chain links valid
```

## 🧪 Weekly Chaos Engineering

**Automated chaos testing** with deterministic breach injection:

### GitHub Actions Workflow
```yaml
# .github/workflows/slot10_weekly_chaos.yml
name: Slot 10 Weekly Chaos & Acceptance
on:
  schedule:
    - cron: "0 6 * * 1"   # Mondays 06:00 UTC
  workflow_dispatch:
```

### Manual Chaos Run
```bash
# Run deterministic chaos scenario
python scripts/slot10_weekly_chaos.py --seed 42 --export-dir artifacts

# Expected flow:
# 1. Start canary deployment (1% → 5% → 25%)
# 2. Inject error rate breach (0.030 > 0.0115 threshold)
# 3. Trigger autonomous rollback
# 4. Export Prometheus metrics snapshot
# 5. Generate JSON report for dashboards
```

**Chaos Artifacts**:
- `artifacts/slot10_metrics.prom` - Prometheus metrics snapshot
- `artifacts/slot10_weekly_chaos.json` - Detailed execution report

**Example Report**:
```json
{
  "start": {"action": "start", "reason": "Initialized at 1.0%"},
  "steps": [
    {"step": "green_0", "action": "promote", "reason": "Promoted to 5.0%"},
    {"step": "breach", "action": "rollback", "reason": "SLO violation: error_rate 0.030 > frozen_baseline 0.010 * 1.15"}
  ],
  "rollback": {
    "success": true,
    "elapsed_s": 0.000001,
    "slot10": true, "slot08": true, "slot04": true,
    "errors": {}
  }
}
```

## 🔧 ACL Governance Monitoring

**Capability-based authorization** with test evidence tracking:

```yaml
# acl/registry.yaml - Governance monitoring
capabilities:
  DEPLOY/GATEKEEPER@1:
    description: "Live health gate evaluation for deployment decisions"
    test_evidence: "slots/slot10_civilizational_deployment/tests/test_gates.py"

  DEPLOY/CANARY@1:
    description: "Progressive canary deployment with autonomous rollback"
    test_evidence: "slots/slot10_civilizational_deployment/tests/test_canary.py"

  DEPLOY/SNAPSHOT_BACKOUT@1:
    description: "Cross-slot recovery coordination with MTTR validation"
    test_evidence: "slots/slot10_civilizational_deployment/tests/test_backout.py"
```

## 📈 Performance Monitoring

### MTTR Guarantees
- **Slot 8 Recovery**: ≤5s autonomous memory corruption recovery
- **Slot 8 Quarantine**: ≤1s activation with operational continuity
- **Slot 10 Rollback**: ≤10s cross-slot coordinated rollback

### Adaptive Thresholds
- **Slot 8 Entropy**: Frozen baseline prevents drift during operations
- **Slot 4 Drift Detection**: O(1) rolling statistics with Bayesian confidence
- **Slot 10 SLO Validation**: Frozen baseline SLO evaluation (1.15x error, 1.10x latency)

## 🚨 Alerting & Dashboards

### Key Alert Conditions
```bash
# System-wide health degradation
slot10_deploy_active == 0 && slot10_rollback_triggered == 1

# SLO violation patterns
rate(slot10_slo_violations[5m]) > 0

# Cross-slot coordination failures
slot10_rollback_triggered == 1 && rollback_success != true
```

### Dashboard Queries
```promql
# Deployment success rate
rate(slot10_deploy_stage_pct[1h]) / rate(slot10_deploy_active[1h])

# Gate evaluation health
avg_over_time(slot10_gate_status[24h])

# System autonomy indicators
(slot08_recovery_mttr < 5) and (slot04_safe_mode_available == 1) and (slot10_canary_ready == 1)
```

## 🔄 Operational Runbooks

### Deployment Rollback Investigation
1. Check audit trail: `cat audit_logs/canary_audit.log | tail -20`
2. Review metrics: `cat artifacts/slot10_metrics.prom`
3. Verify cross-slot health: `PYTHONPATH=. python orchestrator/health_pulse.py`
4. Re-run chaos test: `python scripts/slot10_weekly_chaos.py --seed 42`

### Performance Degradation Response
1. **Slot 8**: Check quarantine status and entropy thresholds
2. **Slot 4**: Validate safe-mode activation and drift detection
3. **Slot 10**: Review gate evaluation and canary progression
4. **System**: Run full test suite validation

---

**🎯 All observability systems support the 4.0/4.0 Processual maturity guarantee with autonomous operation, self-healing capabilities, and comprehensive audit trails for civilizational-scale deployment.**