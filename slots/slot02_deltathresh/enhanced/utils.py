"""Utility helpers for the enhanced processor."""

from __future__ import annotations

import hashlib
from typing import Optional, Tuple

from ..models import ProcessingResult


def validate_content_length(content: str, max_length: int) -> Tuple[bool, Optional[str]]:
    if len(content) > max_length:
        return False, f"Content exceeds maximum length of {max_length} characters"
    return True, None


def create_emergency_bypass(content: str, reason: str) -> ProcessingResult:
    return ProcessingResult(
        content=content,
        action="allow",
        reason_codes=["EMERGENCY_BYPASS"],
        tri_score=1.0,
        layer_scores={},
        processing_time_ms=0.0,
        content_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
    )
