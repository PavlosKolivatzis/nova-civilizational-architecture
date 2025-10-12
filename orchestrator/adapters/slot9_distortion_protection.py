from __future__ import annotations
import logging
from typing import Any, Dict

try:
    from nova.slots.slot09_distortion_protection.hybrid_api import (
        create_hybrid_slot9_api,
        DistortionDetectionRequest,
    )
    ENGINE = create_hybrid_slot9_api()
    AVAILABLE = True
except Exception as exc:  # pragma: no cover - slot optional
    logging.getLogger(__name__).exception(
        "Failed to import Slot 9 distortion protection: %s", exc
    )
    ENGINE = None
    AVAILABLE = False

    class DistortionDetectionRequest:  # type: ignore
        def __init__(self, content: str, context: Dict[str, Any] | None = None):
            self.content = content
            self.context = context or {}


class Slot9DistortionProtectionAdapter:
    """Adapter wrapper for Slot-9 distortion protection system."""

    def __init__(self) -> None:
        self.available = AVAILABLE

    async def detect(
        self, content: str, context: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        if not self.available or not ENGINE:
            return {"status": "unavailable"}
        try:
            req = DistortionDetectionRequest(content=content, context=context or {})
            resp = await ENGINE.detect_distortion(req)
            if hasattr(resp, "dict"):
                return resp.dict()
            return dict(resp) if isinstance(resp, dict) else {"status": getattr(resp, "status", "unknown")}
        except Exception as exc:
            logging.getLogger(__name__).exception(
                "Distortion detection failed: %s", exc
            )
            return {"status": "error"}
