# -*- coding: utf-8 -*-
"""Adapter registry for contract-based routing.

This module exposes all slot adapters from a single location. Adapters are
lightweight wrappers around each slot's core logic and provide a consistent
interface for the orchestrator and tests.
"""

from .slot1_truth_anchor import Slot1TruthAnchorAdapter
from .slot2_deltathresh import Slot2DeltaThreshAdapter
from .slot3_emotional import Slot3EmotionalAdapter
from .slot4_tri import Slot4TRIAdapter
from .slot5_constellation import Slot5ConstellationAdapter
from .slot6_cultural import Slot6Adapter
from .slot7_production_controls import Slot7ProductionControlsAdapter
from .slot8_memory_ethics import Slot8MemoryEthicsAdapter
from .slot9_distortion_protection import Slot9DistortionProtectionAdapter
from .slot10_civilizational import Slot10DeploymentAdapter

__all__ = [
    "Slot1TruthAnchorAdapter",
    "Slot2DeltaThreshAdapter",
    "Slot3EmotionalAdapter",
    "Slot4TRIAdapter",
    "Slot5ConstellationAdapter",
    "Slot6Adapter",
    "Slot7ProductionControlsAdapter",
    "Slot8MemoryEthicsAdapter",
    "Slot9DistortionProtectionAdapter",
    "Slot10DeploymentAdapter",
]
