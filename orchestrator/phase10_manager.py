"""Phase 10 module manager (singleton) for orchestrator."""

from typing import Optional
from nova.phase10.fep import FederatedEthicalProtocol
from nova.phase10.pcr import ProvenanceConsensusRegistry
from nova.phase10.ag import AutonomyGovernor
from nova.phase10.cig import CivilizationalIntelligenceGraph
from nova.phase10.fle import FederatedLearningEngine


class Phase10Manager:
    """Singleton manager for Phase 10 modules."""

    def __init__(self):
        """Initialize all Phase 10 modules."""
        # Load config from environment if available
        import os
        config = {
            "fcq_threshold": float(os.getenv("PHASE10_FCQ_THRESHOLD", "0.90")),
            "tri_min": float(os.getenv("PHASE10_TRI_MIN", "0.80")),
            "eai_target": float(os.getenv("PHASE10_EAI_TARGET", "0.85")),
        }

        self.fep = FederatedEthicalProtocol(config={"fcq_threshold": config["fcq_threshold"]})
        self.pcr = ProvenanceConsensusRegistry()
        self.ag = AutonomyGovernor(config={
            "tri_min": config["tri_min"],
            "eai_target": config["eai_target"],
        })
        self.cig = CivilizationalIntelligenceGraph()
        self.fle = FederatedLearningEngine()

    def update_ag_metrics(self, tri: Optional[float] = None, csi: Optional[float] = None, fcq: Optional[float] = None):
        """Update AG cached metrics from external sources."""
        self.ag.update_metrics(tri=tri, csi=csi, fcq=fcq)


# Singleton instance
_phase10_manager: Optional[Phase10Manager] = None


def get_phase10_manager() -> Phase10Manager:
    """Get or create Phase 10 manager singleton."""
    global _phase10_manager
    if _phase10_manager is None:
        _phase10_manager = Phase10Manager()
    return _phase10_manager
