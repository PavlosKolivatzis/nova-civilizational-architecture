# ruff: noqa: E402
from __future__ import annotations
from src_bootstrap import ensure_src_on_path
ensure_src_on_path()
import logging
from typing import Any, Dict

try:
    from nova.slots.slot10_civilizational_deployment.deployer import InstitutionalNodeDeployer
    from nova.slots.slot10_civilizational_deployment.mls import MetaLegitimacySeal
    from nova.slots.slot10_civilizational_deployment.phase_space import NovaPhaseSpaceSimulator
    from orchestrator.adapters.slot6_cultural import Slot6Adapter
    from orchestrator.adapters.slot4_tri import Slot4TRIAdapter

    ENGINE = InstitutionalNodeDeployer(
        Slot6Adapter(),
        Slot4TRIAdapter(),
        MetaLegitimacySeal(Slot6Adapter()),
        NovaPhaseSpaceSimulator(),
    )
    AVAILABLE = True
except Exception as exc:  # pragma: no cover - slot optional
    logging.getLogger(__name__).exception(
        "Failed to import Slot 10 deployment: %s", exc
    )
    ENGINE = None
    AVAILABLE = False


class Slot10DeploymentAdapter:
    """Adapter wrapper for Slot-10 civilizational deployment."""

    def __init__(self) -> None:
        self.available = AVAILABLE

    async def deploy(
        self,
        institution_name: str,
        institution_type: str,
        payload: Dict[str, Any],
        region: str = "",
    ) -> Dict[str, Any]:
        if not self.available or not ENGINE:
            return {"approved": False, "reason": "unavailable"}
        try:
            result = await ENGINE.deploy(
                institution_name, institution_type, payload, region=region
            )
            if hasattr(result, "dict"):
                return result.dict()
            if hasattr(result, "__dict__"):
                return dict(result.__dict__)
            return result
        except Exception as exc:
            logging.getLogger(__name__).exception("Deployment failed: %s", exc)
            return {"approved": False, "reason": "error"}
