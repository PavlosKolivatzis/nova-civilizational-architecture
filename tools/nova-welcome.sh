#!/usr/bin/env bash
# Nova Welcome — Agent Entry Protocol
# Displays Nova metadata + live runtime state
# Usage: ./tools/nova-welcome.sh [--json|--compact]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

MODE="${1:-human}"

# ============================================================================
# Helper: Extract YAML field (fallback to grep if PyYAML unavailable)
# ============================================================================
yaml_get() {
  local file="$1" key="$2"
  # Try PyYAML first
  if python3 -c "import yaml" 2>/dev/null; then
    python3 -c "import yaml,sys; d=yaml.safe_load(open('$file')); keys='$key'.split('.'); v=d; [v:=v.get(k,{}) for k in keys]; print(v if v and v!={} else '')" 2>/dev/null || echo ""
  else
    # Fallback: grep-based extraction (simple key: value patterns)
    grep "^  $key:" "$file" 2>/dev/null | head -1 | sed 's/^[^:]*: *//' | sed 's/"//g' || echo ""
  fi
}

# ============================================================================
# Gather Live State
# ============================================================================

# Git metadata
GIT_COMMIT=$(git log -1 --format='%h' 2>/dev/null || echo "unknown")
GIT_DATE=$(git log -1 --format='%ai' 2>/dev/null || echo "unknown")
GIT_SUBJECT=$(git log -1 --format='%s' 2>/dev/null || echo "")
GIT_BRANCH=$(git branch --show-current 2>/dev/null || echo "detached")

# Maturity check (silent mode to avoid npm noise)
MATURITY_JSON=$(npm run maturity --silent 2>/dev/null || echo '{"averages":{"overall":null}}')
# Try python3 first (Unix/macOS), fallback to python (Windows)
MATURITY_SCORE=$(echo "$MATURITY_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('averages', {}).get('overall', 'N/A'))" 2>/dev/null || \
                 echo "$MATURITY_JSON" | python -c "import json,sys; d=json.load(sys.stdin); print(d.get('averages', {}).get('overall', 'N/A'))" 2>/dev/null || \
                 echo "N/A")

# Test count (from maturity.yaml if present)
if [ -f "docs/maturity.yaml" ]; then
  TEST_COUNT=$(grep "tests_passed:" docs/maturity.yaml | head -1 | sed 's/.*: *//' || echo "N/A")
else
  TEST_COUNT="N/A"
fi

# Phase label (from .nova/meta.yaml)
if [ -f ".nova/meta.yaml" ]; then
  PHASE=$(grep "^  phase:" .nova/meta.yaml | head -1 | sed 's/.*: *//' | sed 's/"//g' || echo "unknown")
else
  PHASE="unknown"
fi

# Audit findings (from audit_master_summary.md if exists)
if [ -f ".artifacts/audit_master_summary.md" ]; then
  AUDIT_DATE=$(grep -E '^\*\*Audit Period\*\*:' .artifacts/audit_master_summary.md | sed 's/.*: //' || echo "N/A")
else
  AUDIT_DATE="N/A"
fi

# ============================================================================
# Output Modes
# ============================================================================

if [ "$MODE" = "--json" ]; then
  # Machine-readable JSON
  cat <<JSON
{
  "system": {
    "name": "Nova Civilizational Architecture",
    "tagline": "Observe → Canonize → Attest → Publish",
    "phase": "$PHASE"
  },
  "runtime": {
    "git": {
      "commit": "$GIT_COMMIT",
      "date": "$GIT_DATE",
      "branch": "$GIT_BRANCH",
      "subject": "$GIT_SUBJECT"
    },
    "maturity": {
      "score": "$MATURITY_SCORE",
      "test_count": "$TEST_COUNT"
    },
    "audit": {
      "date": "$AUDIT_DATE"
    }
  },
  "learning_path": {
    "primer": "agents/nova_ai_operating_framework.md",
    "architecture": "docs/architecture.md",
    "slot_specs": "docs/slots/",
    "metadata": ".nova/meta.yaml"
  }
}
JSON

elif [ "$MODE" = "--compact" ]; then
  # Single-line status
  echo "Nova | commit=$GIT_COMMIT | phase=$PHASE | maturity=$MATURITY_SCORE | tests=$TEST_COUNT | branch=$GIT_BRANCH"

else
  # Human-readable (default)
  cat <<WELCOME
╔════════════════════════════════════════════════════════════════════════════╗
║                   Nova Civilizational Architecture                         ║
║                  Observe → Canonize → Attest → Publish                     ║
╚════════════════════════════════════════════════════════════════════════════╝

🌟 Welcome to Nova

  Nova is a 10-slot AI governance system implementing provenance-first,
  immutable attestation, and civilizational-scale safety protocols.

📊 Current State

  Phase:     $PHASE
  Commit:    $GIT_COMMIT ($GIT_DATE)
  Branch:    $GIT_BRANCH
  Maturity:  $MATURITY_SCORE (Processual = 4.0)
  Tests:     $TEST_COUNT passing
  Audit:     Last run $AUDIT_DATE

🧭 Quick Start

  1. Read the primer:
     → agents/nova_ai_operating_framework.md
     (Understand: Rule of Sunlight, 3 ledgers, 6 invariants)

  2. Explore the architecture:
     → docs/architecture.md (10-slot system map)
     → docs/slots/*.md (individual slot specs)

  3. Inspect metadata:
     → .nova/meta.yaml (this file is your navigation index)

  4. Verify runtime state:
     → pytest -q -m "not slow"  (run tests)
     → npm run maturity         (check maturity scores)
     → curl localhost:8000/metrics | grep nova_  (if NOVA_ENABLE_PROMETHEUS=1)

🎰 The 10 Slots

  Slot 01: Truth Anchor             Slot 06: Cultural Synthesis
  Slot 02: ΔTHRESH Manager           Slot 07: Production Controls
  Slot 03: Emotional Matrix          Slot 08: Memory Ethics Guard
  Slot 04: TRI Engine                Slot 09: Distortion Protection
  Slot 05: Constellation             Slot 10: Civilizational Deployment

🔐 Agent Protocol

  • Default mode: read-only
  • Consent required for writes (request from Slot10)
  • All actions observable (logged, metered, auditable)
  • Follow: .nova/meta.yaml → agent_protocol section

📚 Deep Dive

  Learn more:
    .nova/meta.yaml           → Full navigation index + learning path
    agents/nova_ai_operating_framework.md → Operating doctrine
    docs/INTERSLOT_CONTRACTS.md → Contract stability model

  Get live state:
    tools/nova-welcome.sh --json     → Machine-readable JSON
    tools/nova-welcome.sh --compact  → Single-line status

╔════════════════════════════════════════════════════════════════════════════╗
║  Nova is self-aware. This metadata reflects its current architecture.     ║
║  To update: edit .nova/meta.yaml (stable) or re-run this script (live).   ║
╚════════════════════════════════════════════════════════════════════════════╝

WELCOME
fi
