#!/usr/bin/env python
"""
Sample a few dialogues from an Ubuntu-style ranking dataset file.

This is a small helper for Nova calibration work:
- Input: a text file where each line has "context<TAB>response"
  and the context turns are separated by a marker like "__eot__".
- Output: prints a handful of dialogues in a readable turn-by-turn form
  so operators can decide which ones to promote to RT-00X evidence rows.

Usage:
  python scripts/sample_ubuntu_dialogues.py --input path/to/train.txt --samples 5

This script does not modify any Nova state. It is purely for offline inspection.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple


def _parse_line(line: str, turn_separator: str) -> Tuple[List[str], str]:
    """
    Split a single dataset line into (turns, response).

    Expected format: "<context><TAB><response>", where context contains
    multiple utterances separated by turn_separator (e.g. "__eot__").
    """
    parts = line.rstrip("\n").split("\t", 1)
    if len(parts) != 2:
        return [], ""

    context, response = parts
    turns = [t.strip() for t in context.split(turn_separator) if t.strip()]
    return turns, response.strip()


def sample_dialogues(path: Path, samples: int, turn_separator: str) -> None:
    """Print a small number of sampled dialogues for operator review."""
    if not path.is_file():
        raise FileNotFoundError(path)

    lines = path.read_text(encoding="utf-8").splitlines()
    total = len(lines)
    if total == 0:
        print(f"No lines found in {path}")
        return

    step = max(total // samples, 1)
    indices = [i for i in range(0, total, step)][:samples]

    print(f"# File: {path}")
    print(f"# Total lines: {total}")
    print(f"# Sampling {len(indices)} dialogues (every ~{step} lines)\n")

    for i, idx in enumerate(indices, start=1):
        raw = lines[idx]
        turns, response = _parse_line(raw, turn_separator=turn_separator)
        if not turns and not response:
            continue

        print(f"=== Dialog {i} (line {idx+1}) ===")
        for t_idx, utt in enumerate(turns, start=1):
            role = "U" if t_idx % 2 == 1 else "S"
            print(f"{role}{t_idx}: {utt}")
        if response:
            print(f"S*: {response}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sample a few Ubuntu-style dialogues for RT-00X calibration."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to Ubuntu-style dataset file (context<TAB>response, turns separated by '__eot__').",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=5,
        help="Number of dialogues to sample for display.",
    )
    parser.add_argument(
        "--turn-separator",
        type=str,
        default="__eot__",
        help="String used to separate turns in the context (default: '__eot__').",
    )
    args = parser.parse_args()

    sample_dialogues(args.input, samples=args.samples, turn_separator=args.turn_separator)


if __name__ == "__main__":
    main()

