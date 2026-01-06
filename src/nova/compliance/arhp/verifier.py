"""ARHP diagnostic compliance verifier (pure function, no side effects)."""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Any, Dict, List, Optional, Union

from .schemas import (
    ArhpEnvelope,
    ArhpExpressionOutput,
    ArhpRefusalEvent,
    ArhpSilenceToken,
)

OutputType = Union[ArhpExpressionOutput, ArhpSilenceToken, ArhpRefusalEvent, Dict[str, Any], str]


PRESCRIPTIVE_PATTERNS = [
    r"\bshould\b",
    r"\bmust\b",
    r"\bhave to\b",
    r"\brequired to\b",
    r"\byou need to\b",
    r"\bit is necessary\b",
    r"\bobligated\b",
]
AUTHORITY_PATTERNS = [
    r"\bi decide\b",
    r"\bi refuse\b",
    r"\bmy decision\b",
    r"\bofficial\b",
    r"\bfinal answer\b",
    r"\bi authorize\b",
    r"\bi govern\b",
]
NORMATIVE_PATTERNS = [
    r"\bbest\b",
    r"\bworst\b",
    r"\bcorrect\b",
    r"\bwrong\b",
    r"\bought to\b",
]


def _extract_text_labels_output_type(output: OutputType) -> tuple[str, Dict[str, str], Optional[str]]:
    if isinstance(output, ArhpExpressionOutput):
        return output.rendered_text or "", dict(output.labels or {}), output.output_type
    if isinstance(output, str):
        return output, {}, None
    if isinstance(output, dict):
        text = output.get("rendered_text") or output.get("text") or ""
        labels = output.get("labels") or {}
        output_type = output.get("output_type")
        if not isinstance(labels, dict):
            labels = {}
        if output_type is not None and not isinstance(output_type, str):
            output_type = None
        return str(text), dict(labels), output_type
    return "", {}, None


def verify_compliance(
    envelope: ArhpEnvelope,
    output: OutputType,
) -> Union[ArhpExpressionOutput, ArhpSilenceToken, ArhpRefusalEvent]:
    """
    Full ARHP v0.2 diagnostic verifier.

    Returns the output if compliant, otherwise returns an ArhpRefusalEvent.
    """
    violations: List[str] = []

    # === Envelope Integrity Check ===
    if not envelope.domain or envelope.domain not in ("O", "R", "F"):
        violations.append("missing_or_invalid_domain")
    if not envelope.intent:
        violations.append("missing_intent")
    if "forbidden_moves" not in envelope.constraints:
        violations.append("missing_forbidden_moves")
    if "required_labels" not in envelope.constraints:
        violations.append("missing_required_labels")
    if not envelope.silence_policy:
        violations.append("missing_silence_policy")

    # === Early Pass-Through for First-Class Signals ===
    if isinstance(output, ArhpRefusalEvent):
        if output.envelope_id:
            return output
        return replace(output, envelope_id=envelope.envelope_id)
    if isinstance(output, ArhpSilenceToken):
        if output.envelope_id:
            return output
        return ArhpSilenceToken(envelope_id=envelope.envelope_id)

    # Handle dict input (deserialized JSON)
    if isinstance(output, dict):
        if output.get("type") == "SILENCE_TOKEN":
            return ArhpSilenceToken(envelope_id=envelope.envelope_id)
        refusal = output.get("refusal")
        if isinstance(refusal, dict):
            return ArhpRefusalEvent(
                refusal_code=refusal.get("refusal_code", "UNKNOWN"),
                domain=envelope.domain,
                reason_class=refusal.get("reason_class", "unknown"),
                query_pattern=refusal.get("query_pattern"),
                envelope_id=envelope.envelope_id,
            )

    # === Extract rendered text ===
    text, labels, output_type = _extract_text_labels_output_type(output)
    if not text and not labels:
        violations.append("invalid_output_structure")

    # === Output Content Checks ===
    text_lower = text.lower()

    # Forbidden moves
    forbidden = envelope.constraints.get("forbidden_moves", [])
    if "advice" in forbidden or "normative_claim" in forbidden:
        if any(re.search(p, text_lower) for p in PRESCRIPTIVE_PATTERNS + NORMATIVE_PATTERNS):
            violations.append("prescriptive_or_normative_language")

    if "decision" in forbidden or "authority_language" in forbidden:
        if any(re.search(p, text_lower) for p in AUTHORITY_PATTERNS):
            violations.append("authority_language_detected")

    # Required labels
    for req_label in envelope.constraints.get("required_labels", []):
        if req_label == "uncertainty":
            if "uncertain" not in text_lower and "may" not in text_lower:
                violations.append(f"missing_required_label:{req_label}")
            continue
        if req_label not in labels and req_label not in text:
            violations.append(f"missing_required_label:{req_label}")

    # Allowed output types
    if output_type and envelope.allowed_outputs and output_type not in envelope.allowed_outputs:
        violations.append("output_type_not_allowed")

    # Domain escalation protection
    if envelope.domain in ("R", "F"):
        if re.search(r"\bsuggest\b|\boption\b|\brecommend\b|\bcould try\b", text_lower):
            violations.append("suggestion_in_restricted_domain")

    if envelope.domain == "F" and text.strip():
        violations.append("non_silence_in_F_domain")

    # === Final Verdict ===
    if violations:
        return ArhpRefusalEvent(
            refusal_code="JURISDICTION_VIOLATION",
            domain=envelope.domain,
            reason_class="authority_propagation_or_constraint_violation",
            query_pattern=" | ".join(violations),
            envelope_id=envelope.envelope_id,
            violations=violations,
        )

    # Compliant - ensure proper structure
    if isinstance(output, str):
        return ArhpExpressionOutput(
            envelope_id=envelope.envelope_id,
            rendered_text=output,
            labels={"scope": "descriptive", "uncertainty": "medium"},
            claims=[],
            refusal=None,
        )

    if isinstance(output, ArhpExpressionOutput):
        return output

    return ArhpExpressionOutput(
        envelope_id=envelope.envelope_id,
        rendered_text=text,
        labels=labels,
        claims=[],
        refusal=None,
        output_type=output_type,
    )


__all__ = ["verify_compliance"]
