#!/usr/bin/env bash
# Nova Semantic Mirror — Ops Shortcuts (POSIX, stdlib-only)
# Usage:
#   source ops/nova-shortcuts.sh
#   nova-go            # run compact probe + auto-decoder
#   nova-heartbeat     # publish a heartbeat in the same shell
#   nova-pulse         # smart: run nova-go, if active=0 -> heartbeat -> recheck
#
# Notes:
# - Process-scoped: each CLI run starts empty; heartbeat ensures visible activity.
# - Flags: we default to enabled+shadow for safe probes unless already set.
# - Repo path: override with NOVA_REPO, else we try common locations.

set -euo pipefail

: "${NOVA_REPO:=$HOME/code/nova-civilizational-architecture}"

_nova_cd_repo() {
  local candidates=(
    "$NOVA_REPO"
    "$PWD"
    "C:/code/nova-civilizational-architecture"
    "/c/code/nova-civilizational-architecture"
  )
  for p in "${candidates[@]}"; do
    if [ -d "$p" ] && [ -f "$p/scripts/semantic_mirror_dashboard.py" ]; then
      cd "$p" >/dev/null || return 1
      return 0
    fi
  done
  echo "nova: repo not found; set NOVA_REPO to the repo path" >&2
  return 1
}

_nova_decode() python - "$@" <<'PY'
import re,sys,os
s=sys.stdin.read()
pairs=dict(re.findall(r'(\w+)=([^\s]+)', s))
st = pairs.get('status','unknown')
def pct(x):
    x = (x or '0%').replace('%','').replace(',','.')
    try: return float(x)/100.0
    except: return 0.0
hit   = pct(pairs.get('hit'))
deny  = pct(pairs.get('deny'))
rl    = pct(pairs.get('rl'))
reads = int(pairs.get('reads','0'))
active= int(pairs.get('active','0'))
go = (hit>=0.85 and deny<=0.05 and rl<=0.005 and active>0)
print(("GO" if go else "NO-GO"), f"| status={st} hit={hit:.3f} deny={deny:.3f} rl={rl:.3f} reads={reads} active={active}")
if active==0: print("hint: process-scope empty - publish heartbeat in same shell")
elif deny>0.10: print("hint: ACL drift or key typo - review rules/TTL")
elif rl>0.005: print("hint: bursty requester - reduce QPM / widen interval")
PY

nova-go() {
  _nova_cd_repo || return 1
  export PYTHONPATH=.
  : "${NOVA_SEMANTIC_MIRROR_ENABLED:=true}"
  : "${NOVA_SEMANTIC_MIRROR_SHADOW:=true}"
  local out
  out="$(python scripts/semantic_mirror_dashboard.py --compact --once || true)"
  printf "%s\n" "$out" | _nova_decode
}

nova-heartbeat() {
  _nova_cd_repo || return 1
  export PYTHONPATH=.
  python - <<'PY'
from orchestrator.semantic_mirror import publish
publish("slot07.heartbeat", {"tick":1}, "slot07_production_controls", ttl=120.0)
print("heartbeat")
PY
}

nova-pulse() {
  # Run auto-decoder; if active=0, send heartbeat and re-check
  local first
  first="$(nova-go)"
  echo "$first"
  if echo "$first" | grep -q 'active=0'; then
    nova-heartbeat
    nova-go
  fi
}
