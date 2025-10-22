#!/usr/bin/env bash
# Capture a sealed Phase 10 reflection snapshot (CLI only, no uvicorn required).
# Produces reflect_v10.json and verifies key invariants with jq.

set -euo pipefail

# --- Phase 10 sealed environment flags ---
export PYTHONPATH="${PYTHONPATH:-$PWD/src}"
export NOVA_FLOW_FABRIC_LAZY_INIT="0"

export NOVA_ENABLE_PROMETHEUS="1"
export NOVA_UNLEARN_ANOMALY="1"

export NOVA_ANR_ENABLED="1"
export NOVA_ANR_LEARN_SHADOW="1"
export NOVA_ANR_STRICT_ON_ANOMALY="1"
export NOVA_ANR_PILOT="0.0"

export NOVA_ENABLE_PROBABILISTIC_CONTRACTS="1"
export NOVA_SLOT10_ENABLED="true"
export NOVA_ENABLE_META_LENS="0"

# Sealed build metadata (update if the attested commit/tag changes)
export NOVA_BUILD_SHA="${NOVA_BUILD_SHA:-932d0b1}"
export NOVA_VERSION="${NOVA_VERSION:-v10.0-complete}"

# Capture reflection snapshot
python -m orchestrator.reflection > reflect_v10.json

# Verify snapshot invariants (jq required)
jq -e '
  .environment.flags.NOVA_ENABLE_PROMETHEUS == "1" and
  .environment.flags.NOVA_UNLEARN_ANOMALY == "1" and
  .environment.flags.NOVA_ANR_ENABLED == "1" and
  .environment.flags.NOVA_ANR_LEARN_SHADOW == "1" and
  .environment.flags.NOVA_ANR_PILOT == "0.0" and
  .environment.flags.NOVA_ENABLE_PROBABILISTIC_CONTRACTS == "1" and
  .environment.flags.NOVA_SLOT10_ENABLED == "true" and
  .environment.flags.NOVA_ENABLE_META_LENS == "0" and
  .environment.flags.NOVA_BUILD_SHA == "'"$NOVA_BUILD_SHA"'" and
  .environment.flags.NOVA_VERSION == "'"$NOVA_VERSION"'" and
  .observation.flow_fabric.initialized == true and
  (.observation.flow_fabric.links | tonumber) >= 9 and
  (.attestations.flow_contracts | length) >= 9
' reflect_v10.json >/dev/null

echo "✔ reflect_v10.json captured and verified."
