#!/usr/bin/env bash
set -euo pipefail
PATTERN='(TODO.*mirror|TODO.*TRI|Replace with actual mirror|NOVA_TRI_COHERENCE|NOVA_PHASE_LOCK)'

if command -v rg >/dev/null 2>&1; then
  if rg -nE "$PATTERN" slots | rg -v '(^|/)slot10' ; then
    echo "::error::Found deprecated mirror/TRI stubs in source."
    exit 1
  fi
else
  if grep -RInE "$PATTERN" slots | grep -vE '(^|/)slot10' ; then
    echo "::error::Found deprecated mirror/TRI stubs in source."
    exit 1
  fi
fi
exit 0