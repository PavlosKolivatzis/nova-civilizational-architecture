# ruff: noqa: E402
from src_bootstrap import ensure_src_on_path
ensure_src_on_path()
import logging
from typing import Any, Dict, List, Optional

try:
    from nova.slots.slot01_truth_anchor.truth_anchor_engine import TruthAnchorEngine

    ENGINE = TruthAnchorEngine()
    AVAILABLE = True
except Exception as exc:  # pragma: no cover - optional slot
    logging.getLogger(__name__).exception(
        "Failed to import Slot 1 truth anchor engine: %s", exc
    )
    ENGINE = None
    AVAILABLE = False

# Try to import enhanced engine for advanced features
try:
    from nova.slots.slot01_truth_anchor.enhanced_truth_anchor_engine import TruthAnchorEngine as EnhancedEngine
    ENHANCED_ENGINE = EnhancedEngine()
    ENHANCED_AVAILABLE = True
except Exception:  # pragma: no cover - enhanced features optional
    ENHANCED_ENGINE = None
    ENHANCED_AVAILABLE = False


class Slot1TruthAnchorAdapter:
    """Adapter wrapper for the Slot-1 Truth Anchor engine."""

    def __init__(self) -> None:
        self.available = AVAILABLE
        self.enhanced_available = ENHANCED_AVAILABLE

    def register(self, anchor_id: str, value: Any, **metadata: Any) -> None:
        if not self.available or not anchor_id:
            return
        try:
            if hasattr(ENGINE, "establish_anchor"):
                ENGINE.establish_anchor(anchor_id, value, **metadata)
            else:
                ENGINE.register(anchor_id, value, **metadata)
        except Exception as exc:  # pragma: no cover - defensive
            logging.getLogger(__name__).exception(
                "Anchor registration failed: %s", exc
            )

    def verify(self, anchor_id: str, value: Any) -> bool:
        if not self.available or not anchor_id:
            return True
        try:
            if hasattr(ENGINE, "verify_anchor"):
                return ENGINE.verify_anchor(anchor_id, value)
            return ENGINE.verify(anchor_id, value)
        except Exception as exc:  # pragma: no cover - defensive
            logging.getLogger(__name__).exception(
                "Anchor verification failed: %s", exc
            )
            return False

    def snapshot(self) -> Dict[str, Any]:
        if not self.available:
            return {}
        try:
            if hasattr(ENGINE, "list_anchors"):
                return ENGINE.list_anchors()
            return ENGINE.snapshot()
        except Exception:  # pragma: no cover - defensive
            return {}

    # Enhanced cryptographic features (requires enhanced engine)
    def establish_cryptographic_anchor(self, domain: str, facts: List[str]) -> Optional[str]:
        """Establish a cryptographic RealityLock anchor with multiple facts."""
        if not self.enhanced_available or not ENHANCED_ENGINE:
            return None
        try:
            return ENHANCED_ENGINE.establish_anchor(domain, facts)
        except Exception as exc:  # pragma: no cover - defensive
            logging.getLogger(__name__).exception(
                "Cryptographic anchor establishment failed: %s", exc
            )
            return None

    def verify_cryptographic_anchor(self, domain: str) -> Optional[Dict[str, Any]]:
        """Verify the cryptographic integrity of a RealityLock anchor."""
        if not self.enhanced_available or not ENHANCED_ENGINE:
            return None
        try:
            return ENHANCED_ENGINE.verify_anchor(domain)
        except Exception as exc:  # pragma: no cover - defensive
            logging.getLogger(__name__).exception(
                "Cryptographic anchor verification failed: %s", exc
            )
            return None

    def list_enhanced_anchors(self) -> List[Dict[str, Any]]:
        """List all cryptographic anchors with verification status."""
        if not self.enhanced_available or not ENHANCED_ENGINE:
            return []
        try:
            return ENHANCED_ENGINE.list_anchors()
        except Exception:  # pragma: no cover - defensive
            return []

    def analyze_content_truth(self, content: str, request_id: str, anchor_domain: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Analyze content for truthfulness using enhanced engine (async wrapper)."""
        if not self.enhanced_available or not ENHANCED_ENGINE:
            return None
        try:
            import asyncio
            # Run the async method in the current thread
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, we can't run another event loop
                return {"error": "async_context_conflict", "request_id": request_id}
            else:
                return loop.run_until_complete(
                    ENHANCED_ENGINE.analyze_content(content, request_id, anchor_domain)
                )
        except Exception as exc:  # pragma: no cover - defensive
            logging.getLogger(__name__).exception(
                "Content truth analysis failed: %s", exc
            )
            return {"error": str(exc), "request_id": request_id}

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics from enhanced engine."""
        if not self.enhanced_available or not ENHANCED_ENGINE:
            return {}
        try:
            return ENHANCED_ENGINE.get_cache_stats()
        except Exception:  # pragma: no cover - defensive
            return {}
