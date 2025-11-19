"""
NOVA Slot 1: Root-Mode Orchestrator Adapter (v1.2)
Pure deterministic anchor operations (no inference, no flow mesh)

Flag-gated: NOVA_SLOT01_ROOT_MODE
- When 1: Root-Mode adapter (this file)
- When 0: Legacy adapter (legacy_adapter.py)
"""

import logging
import os
from typing import Dict, Any, Optional

from .truth_anchor_engine import TruthAnchorEngine

logger = logging.getLogger("slot1_adapter")


class Slot1RootModeAdapter:
    """Root-Mode adapter for Truth Anchor. Immutable anchor lookup/verify/register."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Root-mode: STATIC engine selection — no adaptivity
        self.engine = TruthAnchorEngine(
            secret_key=self.config.get("secret_key"),
            logger=logger,
            storage_path=self.config.get("storage_path"),
        )

        # Performance metrics
        self._total_requests = 0
        self._failed_requests = 0

        logger.info("Slot 1 adapter initialized (root-mode)")

    async def run(self, payload: dict, *, request_id: str) -> Dict[str, Any]:
        """
        Root-Mode API (v1.2):
        Allowed operations:
          - register(anchor_id, value, metadata)
          - lookup(anchor_id)
          - verify(anchor_id, claim)
          - recover(anchor_id)
          - snapshot()
          - export_secret_key()

        No dynamic content analysis.
        No scoring.
        No flow-mesh participation.
        """
        self._total_requests += 1

        op = payload.get("op")
        if not op:
            self._failed_requests += 1
            return {
                "success": False,
                "error": "missing_operation",
                "slot": "slot01_truth_anchor",
            }

        try:
            if op == "register":
                return await self._handle_register(payload)
            elif op == "lookup":
                return await self._handle_lookup(payload)
            elif op == "verify":
                return await self._handle_verify(payload)
            elif op == "recover":
                return await self._handle_recover(payload)
            elif op == "snapshot":
                return await self._handle_snapshot(payload)
            elif op == "export_secret_key":
                return await self._handle_export_secret_key(payload)
            else:
                self._failed_requests += 1
                return {
                    "success": False,
                    "error": "unknown_operation",
                    "slot": "slot01_truth_anchor",
                }
        except Exception as e:
            self._failed_requests += 1
            logger.error(f"Root-mode operation failed: {op} - {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "slot": "slot01_truth_anchor",
            }

    async def _handle_register(self, payload: dict) -> Dict[str, Any]:
        """Register immutable anchor."""
        anchor_id = payload.get("anchor_id")
        value = payload.get("value")
        metadata = payload.get("metadata", {})

        if not anchor_id or value is None:
            return {"success": False, "error": "missing_parameters", "slot": "slot01"}

        self.engine.register(anchor_id, value, **metadata)
        return {"success": True, "status": "ok", "slot": "slot01"}

    async def _handle_lookup(self, payload: dict) -> Dict[str, Any]:
        """Lookup anchor by ID."""
        anchor_id = payload.get("anchor_id")
        if not anchor_id:
            return {"success": False, "error": "missing_anchor_id", "slot": "slot01"}

        record = self.engine._anchors.get(anchor_id)
        return {
            "success": True,
            "found": record is not None,
            "value": record.value if record else None,
            "metadata": record.metadata if record else None,
            "slot": "slot01",
        }

    async def _handle_verify(self, payload: dict) -> Dict[str, Any]:
        """Verify claim against stored anchor."""
        anchor_id = payload.get("anchor_id")
        claim = payload.get("claim")

        if not anchor_id or claim is None:
            return {"success": False, "error": "missing_parameters", "slot": "slot01"}

        valid = self.engine.verify(anchor_id, claim)
        return {"success": True, "valid": valid, "slot": "slot01"}

    async def _handle_recover(self, payload: dict) -> Dict[str, Any]:
        """Attempt anchor recovery."""
        anchor_id = payload.get("anchor_id")
        if not anchor_id:
            return {"success": False, "error": "missing_anchor_id", "slot": "slot01"}

        result = self.engine._recover(anchor_id)
        return {
            "success": True,
            "recovered": result is not None,
            "slot": "slot01",
        }

    async def _handle_snapshot(self, payload: dict) -> Dict[str, Any]:
        """Return engine metrics snapshot."""
        return {
            "success": True,
            "snapshot": self.engine.snapshot(),
            "slot": "slot01",
        }

    async def _handle_export_secret_key(self, payload: dict) -> Dict[str, Any]:
        """Export secret key (operator-only)."""
        key = self.engine.export_secret_key()
        return {
            "success": True,
            "key": key.hex(),
            "slot": "slot01",
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get adapter performance metrics."""
        total = max(1, self._total_requests)
        success_count = self._total_requests - self._failed_requests

        return {
            "total_requests": self._total_requests,
            "failed_requests": self._failed_requests,
            "success_rate": round(success_count / total, 4),
            "success_count": success_count,
        }

    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("Slot 1 adapter shutting down (root-mode)")


# Flag-gated adapter selection
def _is_root_mode_enabled():
    """Check if Root-Mode is enabled (re-read at call-time for tests)."""
    return os.getenv("NOVA_SLOT01_ROOT_MODE", "0").strip() == "1"


def _get_adapter_class():
    """Select adapter based on NOVA_SLOT01_ROOT_MODE flag."""
    if _is_root_mode_enabled():
        logger.info("NOVA_SLOT01_ROOT_MODE=1: Using Root-Mode adapter")
        return Slot1RootModeAdapter
    else:
        logger.info("NOVA_SLOT01_ROOT_MODE=0: Using Legacy adapter (fallback)")
        from .legacy_adapter import Slot1LegacyAdapter
        return Slot1LegacyAdapter


# Global instance (lazy initialization)
_slot1_adapter = None


def _get_slot1_adapter():
    """Get or create slot1 adapter instance."""
    global _slot1_adapter
    if _slot1_adapter is None:
        adapter_cls = _get_adapter_class()
        _slot1_adapter = adapter_cls()
    return _slot1_adapter


async def run(payload: dict, *, request_id: str):
    """Orchestrator entry point (flag-gated)."""
    adapter = _get_slot1_adapter()
    return await adapter.run(payload, request_id=request_id)


async def initialize(config: Optional[Dict[str, Any]] = None):
    """Initialize adapter with configuration (flag-gated)."""
    global _slot1_adapter
    adapter_cls = _get_adapter_class()
    _slot1_adapter = adapter_cls(config)
    return _slot1_adapter


async def shutdown():
    """Clean shutdown (flag-gated)."""
    adapter = _get_slot1_adapter()
    await adapter.shutdown()


# Backward compatibility aliases
slot1_adapter = property(lambda self: _get_slot1_adapter())
Slot1Adapter = Slot1RootModeAdapter  # Default export for Root-Mode
