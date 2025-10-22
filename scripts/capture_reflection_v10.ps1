# Capture a sealed Phase 10 reflection snapshot (CLI only, no uvicorn required).
# Produces reflect_v10.json and optionally verifies key invariants with jq if available.

$env:PYTHONPATH = if ($env:PYTHONPATH) { "$env:PYTHONPATH;$PWD\src" } else { "$PWD\src" }
$env:NOVA_FLOW_FABRIC_LAZY_INIT = "0"

$env:NOVA_ENABLE_PROMETHEUS = "1"
$env:NOVA_UNLEARN_ANOMALY = "1"

$env:NOVA_ANR_ENABLED = "1"
$env:NOVA_ANR_LEARN_SHADOW = "1"
$env:NOVA_ANR_STRICT_ON_ANOMALY = "1"
$env:NOVA_ANR_PILOT = "0.0"

$env:NOVA_ENABLE_PROBABILISTIC_CONTRACTS = "1"
$env:NOVA_SLOT10_ENABLED = "true"
$env:NOVA_ENABLE_META_LENS = "0"

# Sealed build metadata (update if the attested commit/tag changes)
if (-not $env:NOVA_BUILD_SHA) { $env:NOVA_BUILD_SHA = "932d0b1" }
if (-not $env:NOVA_VERSION) { $env:NOVA_VERSION = "v10.0-complete" }

python -m orchestrator.reflection > reflect_v10.json

# Optional verification (requires jq)
if (Get-Command jq -ErrorAction SilentlyContinue) {
  jq -e '
    .environment.flags.NOVA_ENABLE_PROMETHEUS == "1" and
    .environment.flags.NOVA_UNLEARN_ANOMALY == "1" and
    .environment.flags.NOVA_ANR_ENABLED == "1" and
    .environment.flags.NOVA_ANR_LEARN_SHADOW == "1" and
    .environment.flags.NOVA_ANR_PILOT == "0.0" and
    .environment.flags.NOVA_ENABLE_PROBABILISTIC_CONTRACTS == "1" and
    .environment.flags.NOVA_SLOT10_ENABLED == "true" and
    .environment.flags.NOVA_ENABLE_META_LENS == "0" and
    .environment.flags.NOVA_BUILD_SHA == "'"$env:NOVA_BUILD_SHA"'" and
    .environment.flags.NOVA_VERSION == "'"$env:NOVA_VERSION"'" and
    .observation.flow_fabric.initialized == true and
    (.observation.flow_fabric.links | tonumber) -ge 9 and
    (.attestations.flow_contracts | length) -ge 9
  ' reflect_v10.json | Out-Null
}

Write-Host "✔ reflect_v10.json captured$(if (Get-Command jq -ErrorAction SilentlyContinue) { ' and verified' } else { '' })."
