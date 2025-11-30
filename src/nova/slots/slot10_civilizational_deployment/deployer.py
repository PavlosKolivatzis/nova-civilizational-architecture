from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Optional, TYPE_CHECKING

from nova.orchestrator.adapters.slot4_tri import Slot4TRIAdapter
from nova.orchestrator.adapters.slot6_cultural import Slot6Adapter

from .models import (
    DeploymentMetrics,
    DeploymentPhase,
    DeploymentResult,
    MLSDecision,
    ThreatLevel,
)
from .mls import MetaLegitimacySeal
from .phase_space import NovaPhaseSpaceSimulator

if TYPE_CHECKING:  # pragma: no cover - optional dependency
    from frameworks.geometric_memory import GeometricMemory


class InstitutionalNodeDeployer:
    """End-to-end deployment pipeline guarded by Slot-6 validation."""

    def __init__(
        self,
        slot6: Slot6Adapter,
        slot4: Slot4TRIAdapter,
        mls: MetaLegitimacySeal,
        phase_space: NovaPhaseSpaceSimulator,
        geomemory: Optional["GeometricMemory"] = None,
    ) -> None:
        self.slot6 = slot6
        self.slot4 = slot4
        self.mls = mls
        self.phase_space = phase_space
        self.geomemory = geomemory
        self.metrics = DeploymentMetrics()
        level = os.getenv("NOVA_LOG_LEVEL", "INFO").upper()
        self.logger = logging.getLogger("slot10.deployer")
        self.logger.setLevel(level)

    async def _profile(self, institution_name: str, ctx: Dict[str, Any]) -> Any:
        key = f"{institution_name}:{ctx.get('region','')}"
        if self.geomemory and getattr(self.geomemory, "enabled", False):
            try:
                cached = self.geomemory.get(key)
                if cached:
                    return cached
                profile = await asyncio.to_thread(self.slot6.analyze, institution_name, ctx)
                self.geomemory.put(key, profile, ttl_s=300)
                return profile
            except Exception:
                pass
        return await asyncio.to_thread(self.slot6.analyze, institution_name, ctx)

    async def deploy(
        self,
        institution_name: str,
        institution_type: str,
        payload: Dict[str, Any],
        region: str = "",
    ) -> DeploymentResult:
        ctx = {"region": region}
        profile = await self._profile(institution_name, ctx)
        decision, _ = self.mls.assess(profile, institution_type, payload)
        if decision == MLSDecision.QUARANTINE:
            self.metrics.blocked += 1
            return DeploymentResult(
                approved=False,
                reason="guardrail_block",
                transformed=False,
                profile=profile,
                phase=DeploymentPhase.STEALTH_INTEGRATION,
            )
        transformed = decision == MLSDecision.ALLOW_TRANSFORMED

        # consensus capacity check
        if payload.get("capacity_block"):
            self.metrics.blocked += 1
            return DeploymentResult(
                approved=False,
                reason="capacity",
                transformed=transformed,
                profile=profile,
                phase=DeploymentPhase.CONSENSUS,
            )

        # security step
        if payload.get("secure") is False:
            self.metrics.security_failures += 1
            return DeploymentResult(
                approved=False,
                reason="security",
                transformed=transformed,
                profile=profile,
                phase=DeploymentPhase.SECURITY,
            )

        # optional TRI calibration
        if self.slot4.available:
            try:
                await asyncio.wait_for(
                    self.slot4.calibrate({"profile": profile}), timeout=5
                )
            except Exception:
                self.logger.debug("TRI calibration failed", exc_info=True)

        # register node
        self.phase_space.register(institution_name, profile, ThreatLevel.LOW)
        self.metrics.deployments += 1
        return DeploymentResult(
            approved=True,
            reason="registered",
            transformed=transformed,
            profile=profile,
            phase=DeploymentPhase.REGISTER,
        )
