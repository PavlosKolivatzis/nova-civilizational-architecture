#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON:-python}"

echo "🔧 Bootstrapping NOVA developer environment"

echo "📦 Installing pre-commit + detect-secrets (user scope)"
"${PYTHON_BIN}" -m pip install --user --upgrade pre-commit detect-secrets

echo "🪝 Installing git hooks"
pre-commit install

if [[ ! -f ".secrets.baseline" ]]; then
  echo "🧾 No .secrets.baseline detected; generating a fresh baseline (may take a minute)..."
  detect-secrets scan --all-files > .secrets.baseline
  echo "✅ Baseline written to .secrets.baseline (commit it with your change)."
else
  echo "ℹ️  Existing .secrets.baseline found; skipping baseline generation."
fi

echo "▶️  Running hooks across repository (first run warms caches; failures will exit non-zero)"
pre-commit run --all-files || true

echo "🎯 Developer environment bootstrap complete."
