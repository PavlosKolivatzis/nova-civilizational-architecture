from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from slots.slot06_cultural_synthesis.multicultural_truth_synthesis import CulturalProfile



class DeploymentPhase(Enum):
    STEALTH_INTEGRATION = "stealth_integration"
    TRI_CALIBRATION = "tri_calibration"
    CONSENSUS = "consensus_integration"
    SECURITY = "security"
    REGISTER = "register"


class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MLSDecision(Enum):
    ALLOW = "allow"
    ALLOW_TRANSFORMED = "allow_transformed"
    QUARANTINE = "quarantine"


@dataclass
class DeploymentMetrics:
    deployments: int = 0
    blocked: int = 0
    security_failures: int = 0


@dataclass
class DeploymentResult:
    approved: bool
    reason: str
    transformed: bool
    profile: CulturalProfile
    phase: DeploymentPhase
    extra: Any = None
