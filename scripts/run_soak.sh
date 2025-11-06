#!/bin/bash
# Phase 15-8.5 A/B Soak — Runner Script
# Run this in a separate terminal after starting the server

HOST="${1:-127.0.0.1}"
PORT="${2:-8100}"
DURATION="${3:-1800}"  # 30 minutes per combo
STEP="${4:-5}"         # 5 second sampling
OUTPUT="${5:-.artifacts/wisdom_ab_runs.csv}"

echo "========================================"
echo "Starting Phase 15-8.5 A/B Soak Runner"
echo "========================================"
echo ""
echo "Configuration:"
echo "  Host:     $HOST"
echo "  Port:     $PORT"
echo "  Duration: $DURATION seconds ($(($DURATION / 60)) minutes per combo)"
echo "  Step:     $STEP seconds"
echo "  Output:   $OUTPUT"
echo ""
echo "Parameter Grid:"
echo "  κ (kappa): 0.01, 0.02"
echo "  G₀ (g0):   0.55, 0.60, 0.65"
echo "  Total:     6 combinations × $(($DURATION / 60)) min = $(($DURATION * 6 / 60)) minutes"
echo ""
echo "IMPORTANT: You must manually restart the server with new env vars"
echo "           for each combo. See .artifacts/SOAK_LAUNCH_INSTRUCTIONS.md"
echo ""
echo "Starting in 5 seconds..."
sleep 5

python scripts/soak_ab_wisdom_governor.py \
  --host "$HOST" --port "$PORT" \
  --kappa 0.01 0.02 \
  --g0 0.55 0.60 0.65 \
  --dur "$DURATION" --step "$STEP" \
  --out "$OUTPUT"

echo ""
echo "========================================"
echo "Soak Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Summarize: python scripts/summarize_wisdom_ab_runs.py --csv $OUTPUT"
echo "  2. Visualize: python scripts/plot_wisdom_ab_runs.py --csv $OUTPUT"
echo "  3. Review:    cat docs/reflections/phase_15_8_5_ab_report.md"
echo ""
