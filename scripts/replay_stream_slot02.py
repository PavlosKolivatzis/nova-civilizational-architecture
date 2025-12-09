#!/usr/bin/env python
"""
Replay a stored interaction stream through Slot02 (DeltaThreshProcessor)
to observe temporal USM over time.

Input:
  - JSONL file as produced by scripts/export_conversation_stream.py
    Each line: {"stream_id", "turn_index", "role", "text", "timestamp"}

Behavior:
  - Enables bias detection + temporal USM in-process.
  - Uses stream_id as session_id.
  - Prints per-turn:
      turn_index, role, graph_state, collapse_inst,
      H_temporal, rho_temporal, C_temporal, action.
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict

import sys

# Ensure we can import nova.* the same way local probes do
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
for entry in (str(ROOT), str(SRC)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from nova.slots.slot02_deltathresh.core import DeltaThreshProcessor


def replay_stream(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)

    # Ensure flags are on for this run
    os.environ["NOVA_ENABLE_BIAS_DETECTION"] = "1"
    os.environ["NOVA_ENABLE_USM_TEMPORAL"] = "1"
    # Keep whatever NOVA_TEMPORAL_MODE is already set to; default soft in config.

    processor = DeltaThreshProcessor()

    print(f"# Stream file: {path}")
    print(f"# Bias enabled: {processor._bias_detection_enabled}")
    print(f"# Temporal enabled: {processor._temporal_usm_enabled}")
    print()

    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            rec: Dict[str, Any] = json.loads(raw)
            text = rec.get("text") or ""
            stream_id = rec.get("stream_id") or "unknown"
            turn_index = rec.get("turn_index")
            role = rec.get("role") or "unknown"

            result = processor.process_content(text, session_id=stream_id)
            bias = result.bias_report or {}
            temporal = result.temporal_usm

            collapse_inst = bias.get("collapse_score")
            metadata = bias.get("metadata") or {}
            graph_state = metadata.get("graph_state", "unknown")

            if temporal is None:
                H_t = rho_t = C_t = None
            else:
                H_t = temporal.get("H_temporal")
                rho_t = temporal.get("rho_temporal")
                C_t = temporal.get("C_temporal")

            print(
                f"turn={turn_index:>2} role={role:<9} "
                f"state={graph_state:<6} "
                f"C_inst={collapse_inst!s:<6} "
                f"H_t={H_t!s:<6} rho_t={rho_t!s:<6} C_t={C_t!s:<6} "
                f"action={result.action}"
            )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Replay a JSONL interaction stream through Slot02.")
    parser.add_argument(
        "stream_path",
        type=Path,
        help="Path to JSONL stream file (from export_conversation_stream).",
    )
    args = parser.parse_args()
    replay_stream(args.stream_path)


if __name__ == "__main__":
    main()
