# Phase 15-8.5 A/B Soak — Launch Instructions

## Quick Validation (2 minutes)

Test the infrastructure before the full 3-hour run:

### Terminal 1: Start Server
```powershell
$env:NOVA_WISDOM_GOVERNOR_ENABLED="1"
$env:NOVA_WISDOM_BACKPRESSURE_ENABLED="1"
$env:NOVA_WISDOM_TRI_FEEDBACK_ENABLED="1"
$env:NOVA_ENABLE_PROMETHEUS="1"
$env:JWT_SECRET="dev"
$env:NOVA_WISDOM_G_KAPPA="0.01"
$env:NOVA_WISDOM_G_TARGET="0.60"

python -m uvicorn orchestrator.app:app --host 127.0.0.1 --port 8100 --workers 1
```

### Terminal 2: Quick Validation Run
```bash
# 1-minute test with just 2 combos
python scripts/soak_ab_wisdom_governor.py \
  --host 127.0.0.1 --port 8100 \
  --kappa 0.01 0.02 \
  --g0 0.60 \
  --dur 60 --step 5 \
  --out .artifacts/wisdom_ab_validation.csv

# Check output
tail -20 .artifacts/wisdom_ab_validation.csv
```

---

## Full 3-Hour Production Soak

### Option A: Manual Mode (Recommended)

#### Terminal 1: Server (restart with new env vars for each combo)

**Combo 1** — κ=0.01, G₀=0.55 (30 min):
```powershell
$env:NOVA_WISDOM_GOVERNOR_ENABLED="1"
$env:NOVA_WISDOM_BACKPRESSURE_ENABLED="1"
$env:NOVA_WISDOM_TRI_FEEDBACK_ENABLED="1"
$env:NOVA_ENABLE_PROMETHEUS="1"
$env:JWT_SECRET="dev"
$env:NOVA_WISDOM_G_KAPPA="0.01"
$env:NOVA_WISDOM_G_TARGET="0.55"

python -m uvicorn orchestrator.app:app --host 127.0.0.1 --port 8100 --workers 1
```

**After 30 minutes, stop server (Ctrl+C) and restart with:**

**Combo 2** — κ=0.01, G₀=0.60:
```powershell
$env:NOVA_WISDOM_G_KAPPA="0.01"
$env:NOVA_WISDOM_G_TARGET="0.60"
python -m uvicorn orchestrator.app:app --host 127.0.0.1 --port 8100 --workers 1
```

**Combo 3** — κ=0.01, G₀=0.65:
```powershell
$env:NOVA_WISDOM_G_KAPPA="0.01"
$env:NOVA_WISDOM_G_TARGET="0.65"
python -m uvicorn orchestrator.app:app --host 127.0.0.1 --port 8100 --workers 1
```

**Combo 4** — κ=0.02, G₀=0.55:
```powershell
$env:NOVA_WISDOM_G_KAPPA="0.02"
$env:NOVA_WISDOM_G_TARGET="0.55"
python -m uvicorn orchestrator.app:app --host 127.0.0.1 --port 8100 --workers 1
```

**Combo 5** — κ=0.02, G₀=0.60 (current default):
```powershell
$env:NOVA_WISDOM_G_KAPPA="0.02"
$env:NOVA_WISDOM_G_TARGET="0.60"
python -m uvicorn orchestrator.app:app --host 127.0.0.1 --port 8100 --workers 1
```

**Combo 6** — κ=0.02, G₀=0.65:
```powershell
$env:NOVA_WISDOM_G_KAPPA="0.02"
$env:NOVA_WISDOM_G_TARGET="0.65"
python -m uvicorn orchestrator.app:app --host 127.0.0.1 --port 8100 --workers 1
```

#### Terminal 2: Soak Runner (runs continuously)
```bash
python scripts/soak_ab_wisdom_governor.py \
  --host 127.0.0.1 --port 8100 \
  --kappa 0.01 0.02 \
  --g0 0.55 0.60 0.65 \
  --dur 1800 --step 5 \
  --out .artifacts/wisdom_ab_runs.csv
```

**Script will log each combo start**. Manually restart server in Terminal 1 with new env vars for each combo.

---

## After Soak Completes (3 hours)

### Generate Report & Charts

```bash
# 1. Auto-generate results table with PASS/FAIL
python scripts/summarize_wisdom_ab_runs.py \
  --csv .artifacts/wisdom_ab_runs.csv \
  --out docs/reflections/phase_15_8_5_ab_report.md

# 2. Generate 4 PNG charts
python scripts/plot_wisdom_ab_runs.py \
  --csv .artifacts/wisdom_ab_runs.csv \
  --report docs/reflections/phase_15_8_5_ab_report.md \
  --outdir docs/images/phase15-8-5

# 3. Review results
cat docs/reflections/phase_15_8_5_ab_report.md
```

### Select Winner & Tag

```bash
# Update .env.example with selected (κ, G₀)
# Then commit results:

git add docs/reflections/phase_15_8_5_ab_report.md \
        docs/images/phase15-8-5/*.png \
        .env.example

git commit -m "calibration(wisdom): Phase 15-8.5 soak results — selected κ=X, G₀=Y"

git tag -a v15.8.5 -m "Phase 15-8.5: A/B calibration selects κ=X, G₀=Y for optimal stability+creativity"

git push origin main --tags
```

---

## Monitoring During Soak

### Quick Metrics Check (Terminal 3)
```bash
# Check current wisdom metrics
curl -s http://127.0.0.1:8100/metrics | grep -E "nova_wisdom_(eta_current|stability_margin|hopf_distance|generativity)" | grep -v "^#"

# Tail CSV live data
tail -f .artifacts/wisdom_ab_runs.csv
```

### Health Endpoint
```bash
curl -s http://127.0.0.1:8100/health | jq .
```

---

## Expected Results

**Success Criteria** (automated by summarizer):
- S_mean ≥ 0.03
- H_min ≥ 0.02
- |Δη|_mean ≤ 0.01
- G*_mean ≥ 0.6
- σ(G*) < 0.05
- clamp_ratio < 10%

**Timeline**:
- Total: 3 hours (6 combos × 30 min)
- Post-processing: ~2 minutes
- CSV size: ~2160 rows (360 samples per combo)

---

## Troubleshooting

**Server won't start**:
- Check JWT_SECRET is set: `echo $env:JWT_SECRET`
- Check port 8100 is free: `netstat -ano | findstr :8100`

**Metrics show null**:
- Wait 15-30s after server start (poller initialization)
- Check /metrics endpoint: `curl http://127.0.0.1:8100/metrics`

**CSV not growing**:
- Check server is responding: `curl http://127.0.0.1:8100/health`
- Check script hasn't crashed (look for Python traceback in Terminal 2)

---

Generated: 2025-11-05
Phase: 15-8.5 A/B Soak Calibration
