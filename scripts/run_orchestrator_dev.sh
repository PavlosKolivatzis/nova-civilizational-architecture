#!/usr/bin/env bash
# =============================================================================
# Nova Orchestrator - Development Server Launcher (Bash)
# =============================================================================
# Phase 14.6 operational integration - runs orchestrator with Phase 14 flags
#
# Usage:
#   ./scripts/run_orchestrator_dev.sh
#   ./scripts/run_orchestrator_dev.sh --enable-governance  # Enable temporal governance
#   ./scripts/run_orchestrator_dev.sh --port 9000          # Custom port
#
# Rollback: Ctrl+C to stop server
# =============================================================================

set -euo pipefail

# Parse arguments
ENABLE_GOVERNANCE=0
PORT=8000
HOST="127.0.0.1"

while [[ $# -gt 0 ]]; do
    case $1 in
        --enable-governance)
            ENABLE_GOVERNANCE=1
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--enable-governance] [--port PORT] [--host HOST]"
            exit 1
            ;;
    esac
done

# Get script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Set PYTHONPATH to src/ so 'nova' module is importable
export PYTHONPATH="${REPO_ROOT}/src"

# Phase 14 feature flags (metrics-only mode by default)
export NOVA_ENABLE_BIAS_DETECTION=1
export NOVA_ENABLE_USM_TEMPORAL=1
export NOVA_ENABLE_TEMPORAL_GOVERNANCE=${ENABLE_GOVERNANCE}
export NOVA_ENABLE_PROMETHEUS=1  # Enable /metrics endpoint

# Development settings
export NOVA_LOG_LEVEL=INFO
export JWT_SECRET="dev-secret-minimum-32-characters-long-for-testing-only"

echo "====================================================================="
echo "Nova Orchestrator - Development Server (Phase 14.6)"
echo "====================================================================="
echo ""
echo "Configuration:"
echo "  PYTHONPATH:                     $PYTHONPATH"
echo "  NOVA_ENABLE_BIAS_DETECTION:     $NOVA_ENABLE_BIAS_DETECTION"
echo "  NOVA_ENABLE_USM_TEMPORAL:       $NOVA_ENABLE_USM_TEMPORAL"
echo "  NOVA_ENABLE_TEMPORAL_GOVERNANCE: $NOVA_ENABLE_TEMPORAL_GOVERNANCE"
echo "  NOVA_ENABLE_PROMETHEUS:         $NOVA_ENABLE_PROMETHEUS"
echo ""
echo "Server:"
echo "  URL:     http://${HOST}:${PORT}"
echo "  Metrics: http://${HOST}:${PORT}/metrics"
echo "  Health:  http://${HOST}:${PORT}/health"
echo ""
echo "Press Ctrl+C to stop server"
echo "====================================================================="
echo ""

# Start uvicorn with orchestrator app
exec python -m uvicorn nova.orchestrator.app:app --host "$HOST" --port "$PORT" --workers 1
