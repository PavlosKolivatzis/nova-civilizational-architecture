#!/usr/bin/env python3
"""Compact reflection journaling for production monitoring.

Emits compact snapshots suitable for JSONL logging.
Usage: python scripts/journal_reflection.py >> /var/log/nova/consciousness.jsonl
"""

import json
import sys
from orchestrator.reflection import nova_reflect


def main():
    """Generate compact reflection snapshot for logging."""
    try:
        snap = nova_reflect()
        anr = snap["observation"]["anr_probe"]

        out = {
            "t": int(snap["timestamp"]),
            "id": snap.get("snapshot_id") or snap.get("provenance", {}).get("snapshot_id"),
            "route": anr["route"],
            "conf": anr["confidence"],
            "H_bits": anr.get("entropy_bits", anr.get("entropy", 0.0)),
            "decisiveness": anr.get("decisiveness") or snap.get("provenance", {}).get("decisiveness"),
            "slots_ok": snap["observation"]["slots_ok"],
            "slots_total": snap["observation"]["slots_total"],
            "flow": snap["observation"]["flow_fabric"]["status"],
            "prod": snap["claims"]["production_ready"],
            "arch": snap["claims"]["architectural_consciousness"],
        }

        print(json.dumps(out, separators=(",", ":")))
        return 0

    except Exception as e:
        # Log error to stderr, don't break the pipeline
        print(f"journal_reflection error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())