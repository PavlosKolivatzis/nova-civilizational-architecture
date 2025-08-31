from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

from ..bus import EventBus
from ..adapters.slot4_tri import Slot4TRIAdapter
from ..adapters.slot1_truth_anchor import Slot1TruthAnchorAdapter
from ..adapters.slot6_cultural import Slot6Adapter
from frameworks.enums import DeploymentGuardrailResult, AnchorValidationMode
try:  # optional import for geometric memory
    from frameworks.geometric_memory import GeometricMemory
except Exception:  # pragma: no cover - module added later
    GeometricMemory = None  # type: ignore


class NovaOrchestrator:
    """Event-driven orchestrator with feature-flagged Slot-10 deployment."""

    def __init__(
        self,
        bus: Optional[EventBus] = None,
        slot6: Optional[Slot6Adapter] = None,
        slot4: Optional[Slot4TRIAdapter] = None,
        slot1: Optional[Slot1TruthAnchorAdapter] = None,
    ) -> None:
        self.bus = bus or EventBus()
        self.slot6 = slot6 or Slot6Adapter()
        self.slot4 = slot4 or Slot4TRIAdapter()
        self.slot1 = slot1 or Slot1TruthAnchorAdapter()
        self.start_time = time.time()
        level = os.getenv("NOVA_LOG_LEVEL", "INFO").upper()
        self.logger = logging.getLogger("nova.orchestrator")
        self.logger.setLevel(level)
        mode = os.getenv("NOVA_ANCHOR_VALIDATION_MODE", "STRICT").upper()
        self.anchor_validation_mode = AnchorValidationMode[mode] if mode in AnchorValidationMode.__members__ else AnchorValidationMode.STRICT
        self._slot10_enabled = os.getenv("NOVA_SLOT10_ENABLED", "false").lower() == "true"
        self._slot10_available = False
        self.deployer = None
        if self._slot10_enabled:
            self._init_slot10()
        self._register_handlers()

    def _init_slot10(self) -> None:
        try:
            from slots.slot10_civilizational_deployment.deployer import (
                InstitutionalNodeDeployer,
            )
            from slots.slot10_civilizational_deployment.mls import MetaLegitimacySeal
            from slots.slot10_civilizational_deployment.phase_space import (
                NovaPhaseSpaceSimulator,
            )

            gm: Optional[GeometricMemory] = None
            if GeometricMemory is not None and os.getenv("NOVA_GM_ENABLED", "false").lower() == "true":
                gm = GeometricMemory(enabled=True)  # type: ignore[call-arg]
            self.deployer = InstitutionalNodeDeployer(
                self.slot6,
                self.slot4,
                MetaLegitimacySeal(self.slot6),
                NovaPhaseSpaceSimulator(),
                geomemory=gm,
            )
            self._slot10_available = True
        except Exception as exc:  # pragma: no cover - import failures
            self.logger.warning("Slot 10 unavailable: %s", exc)
            self._slot10_available = False

    def _register_handlers(self) -> None:
        self.bus.subscribe("content.validate", self._handle_content_validate)
        self.bus.subscribe("system.status", self._handle_status)
        if self._slot10_available:
            self.bus.subscribe("deploy.node", self._handle_deploy)

    async def _handle_anchor_verification(self, event: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        if not self.slot1.available:
            return True, event
        payload = event.get("payload")
        content = payload.get("content") if isinstance(payload, dict) else None
        anchor_id = event.get("anchor_id")
        if not anchor_id or content is None:
            return True, event
        try:
            valid = self.slot1.verify(anchor_id, content)
        except Exception:
            valid = False
        if valid:
            return True, event
        await self.bus.publish("anchor_verification_failed", {"anchor_id": anchor_id})
        if self.anchor_validation_mode == AnchorValidationMode.STRICT:
            return False, {"result": DeploymentGuardrailResult.BLOCKED_PRINCIPLE_VIOLATION}
        event["anchor_status"] = "FAILED"
        return True, event

    async def _handle_content_validate(self, event: Dict[str, Any]) -> Dict[str, Any]:
        should_continue, event = await self._handle_anchor_verification(event)
        if not should_continue:
            return event
        if self.slot4.available:
            try:
                await asyncio.wait_for(self.slot4.calibrate(event), timeout=5)
            except Exception:
                self.logger.debug("TRI calibration failed", exc_info=True)
        profile = self.slot6.analyze(
            event.get("institution_name", ""), event.get("context", {})
        )
        result = self.slot6.validate(
            profile,
            event.get("institution_type", "generic"),
            event.get("payload", {}),
        )
        if result.result in (
            DeploymentGuardrailResult.APPROVED,
            DeploymentGuardrailResult.REQUIRES_TRANSFORMATION,
        ):
            await self.bus.publish(
                "content.approved", {"profile": profile, "validation": result}
            )
        else:
            await self.bus.publish(
                "content.blocked", {"profile": profile, "validation": result}
            )
        return {"result": result.result}

    async def _handle_deploy(self, event: Dict[str, Any]) -> Any:
        if not self.deployer:
            return {"error": "slot10_disabled"}
        return await self.deployer.deploy(
            event.get("institution_name", ""),
            event.get("institution_type", "generic"),
            event.get("payload", {}),
            region=event.get("region", ""),
        )

    async def _handle_status(self, _: Dict[str, Any]) -> Dict[str, Any]:
        uptime = time.time() - self.start_time
        return {
            "uptime": uptime,
            "bus": self.bus.snapshot(),
            "slots": {
                "slot1_truth_anchor": self.slot1.available,
                "slot4_tri": self.slot4.available,
                "slot6_cultural": self.slot6.available,
                "slot10_deployer": self._slot10_available,
            },
        }

__all__ = ["NovaOrchestrator", "DeploymentGuardrailResult"]
