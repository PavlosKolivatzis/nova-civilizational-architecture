#!/bin/bash
# Monitor wisdom generativity metric

HOST="${1:-127.0.0.1}"
PORT="${2:-8100}"

echo "Monitoring nova_wisdom_generativity..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
  TIMESTAMP=$(date +"%H:%M:%S")
  GSTAR=$(curl -s "http://$HOST:$PORT/metrics" | grep "nova_wisdom_generativity " | grep -v "#" | awk '{print $2}')

  if [ -n "$GSTAR" ]; then
    echo "[$TIMESTAMP] G* = $GSTAR"
  else
    echo "[$TIMESTAMP] G* = (no data)"
  fi

  sleep 5
done
