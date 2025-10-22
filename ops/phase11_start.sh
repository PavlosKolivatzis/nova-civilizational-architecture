#!/usr/bin/env bash
# Phase 11 convenience launcher with 10% ANR pilot defaults.

set -euo pipefail

export NOVA_ANR_ENABLED="${NOVA_ANR_ENABLED:-1}"
export NOVA_ANR_PILOT="${NOVA_ANR_PILOT:-0.10}"
export NOVA_ANR_MAX_FAST_PROB="${NOVA_ANR_MAX_FAST_PROB:-0.15}"
export NOVA_ANR_STRICT_ON_ANOMALY="${NOVA_ANR_STRICT_ON_ANOMALY:-1}"
export NOVA_ANR_LEARN_SHADOW="${NOVA_ANR_LEARN_SHADOW:-1}"

python -m uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000 --workers 1
