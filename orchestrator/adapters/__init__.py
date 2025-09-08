"""Adapter registry for contract-based routing."""

from .slot2_deltathresh import Slot2DeltaThreshAdapter
from .slot8_memory_ethics import Slot8MemoryEthicsAdapter
from .slot9_distortion_protection import Slot9DistortionProtectionAdapter
from .slot10_civilizational import Slot10DeploymentAdapter

__all__ = [
    "Slot2DeltaThreshAdapter",
    "Slot8MemoryEthicsAdapter",
    "Slot9DistortionProtectionAdapter",
    "Slot10DeploymentAdapter",
]
