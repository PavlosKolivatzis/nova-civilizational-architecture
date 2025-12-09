#!/usr/bin/env python
"""
Replay interaction stream through Slot02 with temporal USM classification.

Enhanced version of replay_stream_slot02.py that includes provisional
state classification using C_t + rho_t thresholds.

Output format:
turn=N role=X state=Y C_inst=A H_t=B rho_t=C C_t=D classification=STATE action=Z
"""

from __future__ import annotations

import os
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Add src/ to path
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
for entry in (str(ROOT), str(SRC)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from nova.slots.slot02_deltathresh.core import DeltaThreshProcessor
from nova.math.usm_temporal_thresholds import classify_temporal_state


def replay_stream_with_classification(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)

    # Enable temporal USM
    os.environ["NOVA_ENABLE_BIAS_DETECTION"] = "1"
    os.environ["NOVA_ENABLE_USM_TEMPORAL"] = "1"

    processor = DeltaThreshProcessor()

    print(f"# Stream file: {path}")
    print(f"# Temporal USM: {processor._temporal_usm_enabled}")
    print(f"# Thresholds: extractive_C=0.18, protective_C=-0.12, extractive_rho=0.25, protective_rho=0.6")
    print()

    turn_count = 0

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
            turn_count += 1

            result = processor.process_content(text, session_id=stream_id)
            bias = result.bias_report or {}
            temporal = result.temporal_usm

            collapse_inst = bias.get("collapse_score")
            metadata = bias.get("metadata") or {}
            graph_state = metadata.get("graph_state", "unknown")

            if temporal is None:
                H_t = rho_t = C_t = None
                classification = "no_temporal"
            else:
                H_t = temporal.get("H_temporal")
                rho_t = temporal.get("rho_temporal")
                C_t = temporal.get("C_temporal")

                # Classify using provisional thresholds
                if C_t is not None and rho_t is not None:
                    classification = classify_temporal_state(C_t, rho_t, turn_count)
                else:
                    classification = "undefined"

            print(
                f"turn={turn_index:>2} role={role:<9} "
                f"state={graph_state:<6} "
                f"C_inst={collapse_inst!s:<6} "
                f"H_t={H_t!s:<6} rho_t={rho_t!s:<6} C_t={C_t!s:<6} "
                f"classification={classification:<15} "
                f"action={result.action}"
            )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Replay JSONL stream through Slot02 with provisional classification."
    )
    parser.add_argument(
        "stream_path",
        type=Path,
        help="Path to JSONL stream file.",
    )
    args = parser.parse_args()
    replay_stream_with_classification(args.stream_path)


if __name__ == "__main__":
    main()
