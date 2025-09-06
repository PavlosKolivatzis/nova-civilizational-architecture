"""Adapter registry for orchestrator slots."""
from .slot1_truth_anchor import Slot1TruthAnchorAdapter
from .slot3_emotional import Slot3EmotionalAdapter
from .slot4_tri import Slot4TRIAdapter
from .slot5_constellation import Slot5ConstellationAdapter
from .slot6_cultural import Slot6Adapter
from .slot7_production_controls import Slot7ProductionControlsAdapter

__all__ = [
    "Slot1TruthAnchorAdapter",
    "Slot3EmotionalAdapter",
    "Slot4TRIAdapter",
    "Slot5ConstellationAdapter",
    "Slot6Adapter",
    "Slot7ProductionControlsAdapter",
]
