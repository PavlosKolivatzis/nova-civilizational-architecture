from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from slots.slot02_deltathresh.core import DeltaThreshProcessor
    from slots.slot02_deltathresh.models import ProcessingResult
    ENGINE = DeltaThreshProcessor()
    AVAILABLE = True
except Exception as exc:  # pragma: no cover - slot optional
    logging.getLogger(__name__).exception(
        "Failed to import Slot 2 ΔTHRESH processor: %s", exc
    )
    AVAILABLE = False
    ENGINE = None

    @dataclass
    class ProcessingResult:  # type: ignore
        content: str = ""
        action: str = "allow"
        reason_codes: List[str] = field(default_factory=list)
        tri_score: float = 0.0
        layer_scores: Dict[str, float] = field(default_factory=dict)
        processing_time_ms: float = 0.0
        content_hash: str = ""
        neutralized_content: Optional[str] = None
        quarantine_reason: Optional[str] = None
        timestamp: float = 0.0
        operational_mode: Optional[str] = None
        session_id: str = "default"
        anchor_integrity: float = 1.0
        version: str = "v0"


class Slot2DeltaThreshAdapter:
    """Adapter wrapper for the Slot-2 ΔTHRESH processor."""

    def __init__(self) -> None:
        self.available = AVAILABLE

    def process(self, content: str, session_id: str = "default") -> ProcessingResult:
        if not self.available or not ENGINE:
            return ProcessingResult(content=content, action="allow")
        try:
            return ENGINE.process_content(content, session_id=session_id)
        except Exception:
            logging.getLogger(__name__).exception(
                "ΔTHRESH processing failed", exc_info=True
            )
            return ProcessingResult(content=content, action="error")
