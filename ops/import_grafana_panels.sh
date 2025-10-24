#!/usr/bin/env bash
# Import Phase-11 Grafana panels using the HTTP API.

set -euo pipefail

if [[ -z "${GRAFANA_URL:-}" ]]; then
  echo "GRAFANA_URL is required (e.g. https://grafana.example.com)" >&2
  exit 1
fi

if [[ -z "${GRAFANA_TOKEN:-}" ]]; then
  echo "GRAFANA_TOKEN is required (Grafana API token with dashboard:write scope)" >&2
  exit 1
fi

payload=$(python - <<'PY'
import json, sys, pathlib
dashboard = json.loads(pathlib.Path("docs/grafana/phase11_panels.json").read_text(encoding="utf-8"))
json.dump({"dashboard": dashboard, "overwrite": True}, sys.stdout)
PY
)

curl -sS \
  -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Authorization: Bearer ${GRAFANA_TOKEN}" \
  -H "Content-Type: application/json" \
  --data "${payload}" >/dev/null

echo "Imported Phase-11 dashboard into Grafana at ${GRAFANA_URL}"
