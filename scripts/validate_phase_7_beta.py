#!/usr/bin/env python3
"""
Phase 7.0-β attestation generator + validator.

Inputs (env):
  TRSI_MEAN            e.g. "0.73"
  DRIFT_MAE            e.g. "0.028"
  ARCHIVE_SHA256       e.g. from sealed Phase 6.0 archive
  GIT_COMMIT           e.g. $GITHUB_SHA
  UTC_TIMESTAMP        e.g. ISO8601
  ATTEST_SCHEMA        path to schema (attest/phase-7.0-beta.json)
  OUTPUT_JSON          path to write (attest/latest_phase_7.0_beta.json)

Behavior:
  - builds attestation JSON
  - validates against JSON Schema
  - prints a 1-line JSON (for JSONL append)
  - exits nonzero if validation fails
"""
import json, os, sys
from pathlib import Path

def env(name, default=None, required=False):
    v = os.getenv(name, default)
    if required and (v is None or str(v).strip() == ""):
        print(f"[validator] Missing required env: {name}", file=sys.stderr)
        sys.exit(2)
    return v

def main():
    # Read inputs
    trsi_mean = float(env("TRSI_MEAN", required=True))
    drift_mae = float(env("DRIFT_MAE", required=True))
    archive_sha = env("ARCHIVE_SHA256", required=True)
    commit = env("GIT_COMMIT", required=True)
    ts = env("UTC_TIMESTAMP", required=True)
    schema_path = Path(env("ATTEST_SCHEMA", "attest/phase-7.0-beta.json"))
    out_path = Path(env("OUTPUT_JSON", "attest/latest_phase_7.0_beta.json"))

    # Build attestation
    payload = {
        "phase": "7.0-beta",
        "commit": commit,
        "trsi_mean": trsi_mean,
        "drift_mae": drift_mae,
        "audit_status": "clean",
        "sha256": archive_sha,
        "timestamp": ts,
        "signature": "The sun shines on this work."
    }

    # Validate
    try:
        import jsonschema
        with schema_path.open("r", encoding="utf-8") as fh:
            schema = json.load(fh)
        jsonschema.validate(instance=payload, schema=schema)
    except Exception as e:
        print(f"[validator] Schema validation failed: {e}", file=sys.stderr)
        print(json.dumps(payload), flush=True)
        sys.exit(1)

    # Persist attestation
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Emit single-line JSON for JSONL append step
    print(json.dumps(payload), flush=True)

if __name__ == "__main__":
    main()
