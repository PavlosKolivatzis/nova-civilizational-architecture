# Phase 14 Operational Deployment Guide

**Status:** Phase 14.6 complete (2025-12-10)
**Target:** Operators running Nova with temporal manipulation detection

---

## Quick Start (2 Minutes)

### Start Orchestrator (Metrics-Only Mode)

**Windows PowerShell:**
```powershell
.\scripts\run_orchestrator_dev.ps1
```

**Linux/Mac/Git Bash:**
```bash
./scripts/run_orchestrator_dev.sh
```

**What this does:**
- Sets `PYTHONPATH` to `src/` (makes `nova` module importable)
- Enables Phase 14 flags:
  - `NOVA_ENABLE_BIAS_DETECTION=1` (USM computation)
  - `NOVA_ENABLE_USM_TEMPORAL=1` (temporal smoothing)
  - `NOVA_ENABLE_TEMPORAL_GOVERNANCE=0` (metrics only, no action overrides)
  - `NOVA_ENABLE_PROMETHEUS=1` (metrics endpoint)
- Starts uvicorn server on `http://127.0.0.1:8000`

---

## Verify Deployment

### Check Health
```bash
curl http://127.0.0.1:8000/health
```

### Check Metrics (Phase 14)
```bash
curl http://127.0.0.1:8000/metrics | grep slot02_temporal
```

**Expected metrics:**
- `slot02_temporal_classification_total` (counts by classification type)
- `slot02_temporal_governance_override_total` (should be 0 in metrics-only mode)

---

## Enable Temporal Governance (Experimental)

**Warning:** Sustained extraction detection will trigger quarantine after 5 consecutive turns.

**PowerShell:**
```powershell
.\scripts\run_orchestrator_dev.ps1 -EnableGovernance
```

**Bash:**
```bash
./scripts/run_orchestrator_dev.sh --enable-governance
```

**Monitor override rate:**
```bash
curl http://127.0.0.1:8000/metrics | grep temporal_governance_override
```

**Rollback:** Restart without `-EnableGovernance` flag.

---

## Operational Notes

### Classification States
- **extractive:** C_t > 0.18, ρ_t < 0.25 (unidirectional power flow)
- **consensus:** C_t < -0.12, ρ_t < 0.25 (protective alignment)
- **collaborative:** C_t < -0.12, ρ_t > 0.6 (high reciprocity)
- **neutral:** All other states
- **warming_up:** First 3 turns (insufficient data)

### Thresholds (Provisional)
- C_t extractive: 0.18
- C_t consensus: -0.12
- ρ_t low: 0.25
- ρ_t high: 0.6
- Sustained: 5 consecutive turns

**Status:** Provisional (based on 30-turn pilot). Requires 100-200 sessions for empirical calibration.

### Known Limitations
- Natural language text rarely produces sustained C_t > 0.18
- Most conversations classify as consensus/neutral/collaborative
- Governance logic validated with unit tests (controlled values)
- Real-world threshold accuracy TBD during operational deployment

---

## Rollback Procedures

### Immediate Disable (Metrics-Only → Off)
```bash
# Stop server (Ctrl+C)
# Restart without Phase 14 flags:
export PYTHONPATH="$PWD/src"
export NOVA_ENABLE_BIAS_DETECTION=0
export NOVA_ENABLE_USM_TEMPORAL=0
python -m uvicorn nova.orchestrator.app:app --host 127.0.0.1 --port 8000
```

### Code-Level Rollback
```bash
git revert 913773f  # Phase 14.6 temporal governance
git revert 3362ed1  # Phase 14.6 spec updates + Prometheus fix
# Tests still pass (Phase 14.5 baseline intact)
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'nova'`
**Cause:** PYTHONPATH not set
**Fix:** Use launcher scripts or set `export PYTHONPATH="$PWD/src"` before running

### Metrics endpoint returns 404
**Cause:** `NOVA_ENABLE_PROMETHEUS=0`
**Fix:** Restart with `NOVA_ENABLE_PROMETHEUS=1`

### No temporal metrics visible
**Cause:** Bias detection disabled
**Fix:** Verify `NOVA_ENABLE_BIAS_DETECTION=1` and `NOVA_ENABLE_USM_TEMPORAL=1`

### All classifications show "warming_up"
**Cause:** Turn count < 3 or session state not persisting
**Fix:** Send multiple turns (4+) with same session ID

---

## Next Steps

**Week 1-2:** Operational validation
- Run 20-50 test conversations
- Export classification distribution
- Validate thresholds with real data

**Week 3-4:** Calibration
- Refine thresholds based on false positive rate
- Document empirical distributions
- Update `usm_temporal_thresholds.py` if needed

**Phase 14.7:** Advanced features (future)
- ρ_t velocity triggers (sudden drop detection)
- Turn-count adaptive thresholds
- Domain-specific calibration

---

**Reference:**
- Full spec: `docs/specs/phase14_6_temporal_governance.md`
- Retrospective: `docs/specs/phase14_retrospective.md`
- Test suite: `tests/slot02/test_temporal_governance*.py`
