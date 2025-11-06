#!/bin/bash
# Workload generation for wisdom governor calibration

HOST="${1:-127.0.0.1}"
PORT="${2:-8100}"

echo "Starting FEP workload loop..."
echo "Press Ctrl+C to stop"
echo ""

COUNTER=0
while true; do
  COUNTER=$((COUNTER + 1))
  curl -s -X POST "http://$HOST:$PORT/phase10/fep/proposal" \
    -H "Content-Type: application/json" \
    -d '{"decision_id":"test-'"$COUNTER"'","topic":"loadtest"}' \
    | head -c 100
  echo ""
  sleep 2
done
