#!/usr/bin/env python
"""
Find conversations in the Anthropic export whose messages contain a given substring.

Usage:
  python scripts/find_conversation_by_text.py --contains "Cognitive Sovereignty Framework"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def find_conversations(conversations_path: Path, needle: str) -> List[Dict[str, Any]]:
    if not conversations_path.is_file():
        raise FileNotFoundError(conversations_path)

    data = json.loads(conversations_path.read_text(encoding="utf-8"))
    needle_lower = needle.lower()
    results: List[Dict[str, Any]] = []

    for conv in data:
        for msg in conv.get("chat_messages", []):
            text = (msg.get("text") or "").lower()
            if needle_lower in text:
                results.append(
                    {
                        "uuid": conv.get("uuid"),
                        "name": conv.get("name") or "",
                        "message_uuid": msg.get("uuid"),
                    }
                )
                break

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Search conversations.json for a substring.")
    parser.add_argument(
        "--contains",
        required=True,
        help="Substring to search for in message text.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("archive") / "AI data history" / "conversations.json",
        help="Path to conversations.json export.",
    )
    args = parser.parse_args()

    matches = find_conversations(args.input, args.contains)
    print(f"matches: {len(matches)}")
    for m in matches:
        print(f"{m['uuid']} | {m['name']} | msg={m['message_uuid']}")


if __name__ == "__main__":
    main()

