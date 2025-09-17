from __future__ import annotations

import json
import hashlib
from typing import Any, Mapping

# Fields we know about (ordered), plus a catch-all for anything else.
_CANON_ORDER = (
    "id",
    "slot",
    "type",
    "timestamp",
    "api_version",
    "router_state",
    "circuit_breaker_state",
    "ids_traits_state",
    "ids_content_state",
    "data",
    "confidence",
    "previous_hash",
    "extra",
)


def _canon(v: Any) -> str:
    if isinstance(v, (dict, list, tuple)):
        # Deterministic + compact; sorting only where needed
        return json.dumps(v, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    return str(v)


def compute_audit_hash(record: Mapping[str, Any]) -> str:
    """Compute a deterministic hash over all fields of an audit record."""
    parts = []
    present = set()
    for k in _CANON_ORDER:
        if k in record:
            parts.append(f"{k}={_canon(record[k])}")
            present.add(k)
    for k in sorted(k for k in record.keys() if k not in present):
        parts.append(f"{k}={_canon(record[k])}")
    payload = "|".join(parts)
    return hashlib.blake2b(payload.encode("utf-8"), digest_size=32).hexdigest()
