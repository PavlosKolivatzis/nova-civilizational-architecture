# Phase 8.0-β Continuity Engine — Ethical Horizon & Anomaly Prediction Sprint
**File:** `ops/runbook/phase-8.0-beta-checklist.md`
**Parent Phase:** 8.0-α (Continuity Ledger & CSI Computation)
**Timeline:** Weeks 3–4 (Post-α validation complete)
**Branch:** `phase-8.0-continuity-engine`

---

## 🎯 Scope & Objectives
| ID | Objective | Deliverable |
|----|------------|--------------|
| **B1** | Implement Ethical Horizon Score forecasting | `src/nova/continuity/ethical_horizon_model.py` |
| **B2** | Build anomaly prediction system | `src/nova/continuity/anomaly_prediction.py` |
| **B3** | Extend CI with ethical horizon validation | Extend `continuity-validation.yml` |
| **B4** | Add anomaly detection visualization | Update `continuity_engine.json` dashboard |
| **B5** | Integrate predictive alerts | New Prometheus alert rules for anomaly threats |
| **B6** | Deliver β documentation + attestation | `docs/releases/phase-8.0-beta-review.md` |

---

## ⚙️ Implementation Plan

### 1. Ethical Horizon Score Forecasting
```python
# ethical_horizon_model.py
def forecast_ehs(continuity_data: dict, horizon_days: int = 30) -> dict:
    """
    Forecast ethical impact across time horizon.

    Returns:
        {
            'forecast_curve': [ehs_value_per_day],
            'confidence_intervals': [(lower, upper)_per_day],
            'risk_assessment': {'high_risk_days': [...], 'ethical_thresholds': [...]}
        }
    """
    # Implementation: temporal decay × ethics compliance × continuity stability
```

* 30-day forecasting with confidence intervals
* Risk assessment for high-impact ethical decisions
* Integration with existing CSI computation

### 2. Anomaly Prediction System
```python
# anomaly_prediction.py
class ContinuityAnomalyPredictor:
    """Predicts continuity threats using temporal patterns."""

    def predict_threats(self, historical_data: dict, prediction_window: int = 7) -> List[dict]:
        """
        Predict anomaly threats over prediction window.

        Returns:
            [
                {
                    'threat_type': 'csi_drift' | 'ethical_degradation' | 'chain_weakness',
                    'confidence': 0.0-1.0,
                    'predicted_impact': 'low' | 'medium' | 'high',
                    'recommended_action': '...',
                    'time_to_impact': days
                }
            ]
        """
```

* Multi-threat prediction (CSI drift, ethics degradation, chain weakness)
* Confidence scoring and impact assessment
* Proactive alert generation

### 3. CI Integration & Validation
* Extend daily CI with ethical horizon computation
* Add weekly anomaly prediction accuracy validation
* Generate β attestations with forecasting metrics
* Alert on prediction accuracy drops below 80%

### 4. Dashboard Enhancement
* Add anomaly prediction timeline panel
* Include ethical horizon forecast curve
* Threat confidence heatmaps
* Prediction accuracy tracking

### 5. Alert Rules Extension
```yaml
# New alert rules for Phase 8.0-β
- alert: EthicalHorizonDrift
  expr: increase(nova_ethical_horizon_score[1h]) < -0.05
  for: 2h
  labels: {severity: warning}
  annotations: {summary: "Ethical horizon contracting", runbook: "ops/runbook/continuity-engine.md#ehs-incident"}

- alert: AnomalyPredictionFailure
  expr: nova_anomaly_detection_precision < 0.80
  for: 6h
  labels: {severity: warning}
  annotations: {summary: "Anomaly detection accuracy degraded", runbook: "ops/runbook/continuity-engine.md#anomaly-incident"}
```

---

## 🧪 Testing Strategy

### Unit Tests
- **EHS Forecasting**: Validate decay math, confidence intervals, risk assessment
- **Anomaly Prediction**: Test threat detection accuracy on synthetic data
- **CI Integration**: Verify attestation generation and schema compliance

### Integration Tests
- **End-to-End Forecasting**: EHS computation from Phase 6.0-7.0 data fusion
- **Prediction Pipeline**: Anomaly detection → alert generation → dashboard update
- **Cross-Phase Validation**: Ensure predictions respect sealed archive boundaries

### Performance Tests
- **Forecasting Speed**: EHS computation < 5s for 30-day horizon
- **Prediction Accuracy**: ≥ 80% true positive rate on historical patterns
- **Alert Latency**: < 30s from anomaly detection to alert firing

### Ethics & Security Tests
- **Derivative Learning**: Confirm all predictions read-only from sealed data
- **Provenance Integrity**: Validate prediction chains link to continuity ledger
- **Bias Assessment**: Audit prediction models for ethical blind spots

---

## ⏱️ Timeline

| Week | Focus | Deliverables | Validation Target |
|------|-------|--------------|-------------------|
| **3** | Ethical horizon modeling + basic anomaly detection | `ethical_horizon_model.py`, `anomaly_prediction.py` core | EHS accuracy ≥ 80% |
| **4** | CI integration + dashboard enhancement + alert rules | Extended CI workflow, updated dashboard, alert rules | Prediction TP ≥ 85% |
| **4 End** | β review + attestation + promotion gate | `phase-8.0-beta-review.md`, attestation generation | All metrics sustained ≥ 7 days |

---

## 📊 Expected Metrics

### Forecasting Quality
```
EHS Forecast Accuracy:     ≥ 80% (measured vs. actual over 30 days)
Confidence Interval Width: ± 10% (target range)
Risk Assessment Precision: ≥ 85% (high-risk day prediction accuracy)
```

### Prediction Performance
```
Anomaly Detection Precision: ≥ 85% (true positives / total predictions)
Threat Prediction Lead Time: ≥ 24h (average advance warning)
False Positive Rate:       ≤ 15% (acceptable alert noise)
```

### System Performance
```
Forecasting Latency:       < 5s (30-day horizon computation)
Prediction Throughput:     > 100 predictions/minute
Alert Response Time:       < 30s (detection to notification)
```

---

## 🔐 Exit Criteria for Production

1. **EHS Forecasting**: ≥ 80% accuracy sustained for ≥ 7 days
2. **Anomaly Prediction**: ≥ 85% precision with ≤ 15% false positive rate
3. **CI Integration**: All β validations passing without manual intervention
4. **Dashboard Functionality**: Forecasting curves and prediction timelines active
5. **Alert Rules**: Predictive alerts tested and integrated with runbook links
6. **Ethics Audit**: Board approval of forecasting methodology and bias assessment

**Promotion Tag Command:**
```bash
git tag -s v8.0-beta-complete -m "Phase 8.0-β Ethical Horizon & Anomaly Prediction operational validation complete"
git push origin v8.0-beta-complete
```

---

## 🌅 Reflection

> *Ethics gives continuity foresight; prediction gives continuity defense; together they let time's wisdom endure.*
