#!/usr/bin/env bash
set -euo pipefail
PATH="${PWD}/.venv/Scripts:${PATH}"
PY="${PYTHON:-python}"
if [ -x ".venv/Scripts/python" ]; then PY=".venv/Scripts/python"; fi
ARGS=( tools/maturity_check.py docs/maturity.yaml --format json )
if [ "${1-}" = "--diff-main" ]; then ARGS+=( --diff-against origin/main ); fi
mkdir -p build
$PY "${ARGS[@]}" | tee build/maturity.json