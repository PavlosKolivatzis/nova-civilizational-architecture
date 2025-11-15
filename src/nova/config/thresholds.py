"""Validated configuration objects for adaptive wisdom thresholds.

This module centralizes parsing + validation for stability/generativity thresholds
so all consumers operate with the same, safe ranges (Phase 2.2 audit follow-up).
"""

from __future__ import annotations

import os
from functools import lru_cache as _lru_cache
from typing import Tuple as _Tuple

from pydantic import (
    BaseModel as _BaseModel,
    ConfigDict as _ConfigDict,
    Field as _Field,
    ValidationInfo as _ValidationInfo,
    field_validator as _field_validator,
    model_validator as _model_validator,
)

__all__ = [
    "WisdomThresholds",
    "FederationThresholds",
    "load_wisdom_thresholds",
    "load_federation_thresholds",
]


class WisdomThresholds(_BaseModel):
    """Adaptive wisdom governor thresholds with validation & ordering constraints."""

    critical_margin: float = _Field(
        default=0.01,
        ge=0.005,
        le=0.02,
        description="Stability margin below which learning freezes (CRITICAL mode)",
    )
    stabilizing_margin: float = _Field(
        default=0.02,
        ge=0.01,
        le=0.05,
        description="Margin that triggers stabilizing mode",
    )
    exploring_margin: float = _Field(
        default=0.10,
        ge=0.05,
        le=0.20,
        description="High stability margin enabling exploration mode",
    )
    optimal_margin: float = _Field(
        default=0.05,
        ge=0.03,
        le=0.10,
        description="Stability margin for optimal balance mode",
    )
    exploring_g: float = _Field(
        default=0.60,
        ge=0.40,
        le=0.80,
        description="Generativity threshold at which exploration may engage",
    )
    optimal_g: float = _Field(
        default=0.70,
        ge=0.60,
        le=0.90,
        description="Generativity threshold that sustains optimal mode",
    )

    @_field_validator("stabilizing_margin")
    def _stabilizing_above_critical(cls, value: float, info: _ValidationInfo) -> float:
        critical = info.data.get("critical_margin") if info.data else None
        if critical is not None and value <= critical:
            raise ValueError(
                f"stabilizing_margin ({value:.3f}) must exceed critical_margin ({critical:.3f})"
            )
        return value

    @_field_validator("optimal_margin")
    def _optimal_below_exploring(cls, value: float, info: _ValidationInfo) -> float:
        exploring = info.data.get("exploring_margin") if info.data else None
        if exploring is not None and value >= exploring:
            raise ValueError(
                f"optimal_margin ({value:.3f}) must remain below exploring_margin ({exploring:.3f})"
            )
        stabilizing = info.data.get("stabilizing_margin") if info.data else None
        if stabilizing is not None and value <= stabilizing:
            raise ValueError(
                f"optimal_margin ({value:.3f}) must exceed stabilizing_margin ({stabilizing:.3f})"
            )
        return value

    @_field_validator("optimal_g")
    def _optimal_g_above_exploring(cls, value: float, info: _ValidationInfo) -> float:
        exploring = info.data.get("exploring_g") if info.data else None
        if exploring is not None and value < exploring:
            raise ValueError(
                f"optimal_g ({value:.3f}) must be >= exploring_g ({exploring:.3f}) for consistent gating"
            )
        return value

    @_model_validator(mode="after")
    def _validate_margin_order(self) -> WisdomThresholds:
        ordering: _Tuple[_Tuple[str, float], ...] = (
            ("critical_margin", self.critical_margin),
            ("stabilizing_margin", self.stabilizing_margin),
            ("optimal_margin", self.optimal_margin),
            ("exploring_margin", self.exploring_margin),
        )
        for (name_a, value_a), (name_b, value_b) in zip(ordering, ordering[1:]):
            if value_a >= value_b:
                raise ValueError(
                    "Invalid margin ordering detected: "
                    f"{name_a} ({value_a:.3f}) must remain below {name_b} ({value_b:.3f})"
                )
        return self

    model_config = _ConfigDict(frozen=True, extra="forbid")


class FederationThresholds(_BaseModel):
    """Validated thresholds for federation remediation."""

    backoff_multiplier: float = _Field(
        default=2.0,
        ge=1.5,
        le=4.0,
        description="Multiplier applied when backing off remediation polling interval",
    )

    model_config = _ConfigDict(frozen=True, extra="forbid")


def _wisdom_env_values() -> dict[str, str]:
    """Return raw environment values for wisdom thresholds."""
    return {
        "NOVA_WISDOM_CRITICAL_MARGIN": os.getenv("NOVA_WISDOM_CRITICAL_MARGIN", "0.01"),
        "NOVA_WISDOM_STABILIZING_MARGIN": os.getenv("NOVA_WISDOM_STABILIZING_MARGIN", "0.02"),
        "NOVA_WISDOM_EXPLORING_MARGIN": os.getenv("NOVA_WISDOM_EXPLORING_MARGIN", "0.10"),
        "NOVA_WISDOM_OPTIMAL_MARGIN": os.getenv("NOVA_WISDOM_OPTIMAL_MARGIN", "0.05"),
        "NOVA_WISDOM_EXPLORING_G": os.getenv("NOVA_WISDOM_EXPLORING_G", "0.60"),
        "NOVA_WISDOM_OPTIMAL_G": os.getenv("NOVA_WISDOM_OPTIMAL_G", "0.70"),
    }


def _federation_env_values() -> dict[str, str]:
    """Return raw environment values for federation thresholds."""
    return {
        "NOVA_FEDERATION_BACKOFF_MULTIPLIER": os.getenv("NOVA_FEDERATION_BACKOFF_MULTIPLIER", "2.0"),
    }


@_lru_cache()
def load_wisdom_thresholds() -> WisdomThresholds:
    """Load & validate adaptive wisdom thresholds from environment variables."""
    raw = _wisdom_env_values()
    try:
        return WisdomThresholds(
            critical_margin=float(raw["NOVA_WISDOM_CRITICAL_MARGIN"]),
            stabilizing_margin=float(raw["NOVA_WISDOM_STABILIZING_MARGIN"]),
            exploring_margin=float(raw["NOVA_WISDOM_EXPLORING_MARGIN"]),
            optimal_margin=float(raw["NOVA_WISDOM_OPTIMAL_MARGIN"]),
            exploring_g=float(raw["NOVA_WISDOM_EXPLORING_G"]),
            optimal_g=float(raw["NOVA_WISDOM_OPTIMAL_G"]),
        )
    except ValueError as exc:
        raise ValueError(
            "CRITICAL: Invalid adaptive wisdom threshold configuration detected. "
            f"{exc}\nCurrent values: {raw}\nRefer to .env.example for safe ranges."
        ) from exc


@_lru_cache()
def load_federation_thresholds() -> FederationThresholds:
    """Load & validate federation remediation thresholds."""
    raw = _federation_env_values()
    try:
        return FederationThresholds(
            backoff_multiplier=float(raw["NOVA_FEDERATION_BACKOFF_MULTIPLIER"]),
        )
    except ValueError as exc:
        raise ValueError(
            "CRITICAL: Invalid federation remediation configuration detected. "
            f"{exc}\nCurrent NOVA_FEDERATION_BACKOFF_MULTIPLIER={raw['NOVA_FEDERATION_BACKOFF_MULTIPLIER']}. "
            "Refer to .env.example for safe ranges."
        ) from exc
