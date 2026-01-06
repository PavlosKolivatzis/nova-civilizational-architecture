"""ARHP diagnostic schemas (non-authoritative)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

ArhpDomain = Literal["O", "R", "F"]
ArhpIntent = Literal["render", "explain", "observe", "refuse"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ArhpEnvelope:
    envelope_id: str
    timestamp: str
    domain: ArhpDomain
    intent: ArhpIntent
    constraints: Dict[str, List[str]]
    allowed_outputs: List[str]
    silence_policy: Dict[str, str]
    provenance: Optional[Dict[str, object]] = None


@dataclass
class ArhpRefusalEvent:
    refusal_code: str
    domain: ArhpDomain
    reason_class: str
    event_type: str = "arhp_refusal_event"
    query_pattern: Optional[str] = None
    envelope_id: Optional[str] = None
    timestamp: str = field(default_factory=_utc_now)
    previous_hash: Optional[str] = None
    event_hash: Optional[str] = None
    violations: List[str] = field(default_factory=list)


@dataclass
class ArhpExpressionOutput:
    envelope_id: str
    rendered_text: Optional[str]
    labels: Dict[str, str] = field(default_factory=dict)
    claims: List[Dict[str, object]] = field(default_factory=list)
    refusal: Optional[ArhpRefusalEvent] = None
    output_type: Optional[str] = None


@dataclass(frozen=True)
class ArhpSilenceToken:
    envelope_id: str
    type: str = "SILENCE_TOKEN"
    meaning: str = "No expression permitted under current envelope"


__all__ = [
    "ArhpDomain",
    "ArhpIntent",
    "ArhpEnvelope",
    "ArhpRefusalEvent",
    "ArhpExpressionOutput",
    "ArhpSilenceToken",
]
