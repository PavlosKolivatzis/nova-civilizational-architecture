#!/usr/bin/env python
"""
Export a single archived conversation into a Nova-style interaction stream.

Input:
  - archive/AI data history/conversations.json (Anthropic-style export)

Output:
  - data/interactions/<conversation_uuid>.jsonl

Each line in the output JSONL has:
  - stream_id: conversation UUID (opaque)
  - turn_index: 1-based index within the conversation
  - role: "user" or "assistant"
  - text: flattened text content of the message
  - timestamp: message created_at ISO string
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def _flatten_text(msg: Dict[str, Any]) -> str:
    """Get a reasonable text representation for a chat message."""
    text = (msg.get("text") or "").strip()
    if text:
        return text

    parts: List[str] = []
    for segment in msg.get("content", []):
        if segment.get("type") == "text":
            seg_text = (segment.get("text") or "").strip()
            if seg_text:
                parts.append(seg_text)
    return "\n".join(parts)


def export_conversation(conversations_path: Path, output_dir: Path, conv_uuid: str) -> Path:
    """Export the specified conversation UUID to a JSONL stream file."""
    if not conversations_path.is_file():
        raise FileNotFoundError(conversations_path)

    data = json.loads(conversations_path.read_text(encoding="utf-8"))

    conv = next((c for c in data if c.get("uuid") == conv_uuid), None)
    if conv is None:
        raise SystemExit(f"Conversation {conv_uuid} not found in {conversations_path}")

    messages = conv.get("chat_messages", [])
    # They are usually in order already, but sort by created_at defensively.
    messages = sorted(messages, key=lambda m: m.get("created_at", ""))

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{conv_uuid}.jsonl"

    stream_id = conv_uuid
    with out_path.open("w", encoding="utf-8") as f:
        for idx, msg in enumerate(messages, start=1):
            sender = msg.get("sender")
            if sender == "human":
                role = "user"
            elif sender == "assistant":
                role = "assistant"
            else:
                # Unknown sender type; keep it but label generically.
                role = sender or "unknown"

            record = {
                "stream_id": stream_id,
                "turn_index": idx,
                "role": role,
                "text": _flatten_text(msg),
                "timestamp": msg.get("created_at"),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export one conversation to a Nova interaction stream.")
    parser.add_argument(
        "--uuid",
        required=True,
        help="Conversation UUID to export (as found in conversations.json).",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("archive") / "AI data history" / "conversations.json",
        help="Path to conversations.json export.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data") / "interactions",
        help="Directory to write JSONL stream into.",
    )
    args = parser.parse_args()

    out = export_conversation(args.input, args.output_dir, args.uuid)
    print(out)


if __name__ == "__main__":
    main()

