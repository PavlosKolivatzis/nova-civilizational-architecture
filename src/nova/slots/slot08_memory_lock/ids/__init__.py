"""Intrusion Detection System components for Slot 8."""

from .detectors import (
    SurgeDetector,
    ForbiddenPathDetector,
    TamperDetector,
    ReplayDetector,
    IDSDetectorSuite
)

__all__ = [
    "SurgeDetector",
    "ForbiddenPathDetector",
    "TamperDetector",
    "ReplayDetector",
    "IDSDetectorSuite"
]
