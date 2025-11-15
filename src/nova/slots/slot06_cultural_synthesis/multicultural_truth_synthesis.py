from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any, Dict, Iterator, Optional
from warnings import warn

from .adapter import CulturalSynthesisAdapter
from .engine import CulturalProfile, CulturalSynthesisEngine

# --- legacy import hard gate ---

def _env_truthy(name: str) -> bool:
    v = os.getenv(name, "")
    return v.strip() == "1"

if _env_truthy("NOVA_BLOCK_LEGACY_SLOT6"):
    raise ImportError(
        "Legacy Slot6 API is disabled (NOVA_BLOCK_LEGACY_SLOT6). "
        "Use engine.CulturalSynthesisEngine and adapter.CulturalSynthesisAdapter."
    )
# --- rest of file (aliases, ProfileWrapper, etc.) ---

# Legacy usage tracking for retirement planning
_LEGACY_CALL_COUNT = 0

def _increment_legacy_usage():
    """Track legacy usage for retirement metrics."""
    global _LEGACY_CALL_COUNT
    _LEGACY_CALL_COUNT += 1

    # Also record in centralized metrics if available
    try:
        from orchestrator.metrics import get_slot6_metrics
        get_slot6_metrics().record_legacy_call()
    except ImportError:
        # Centralized metrics not available, use local counter only
        pass

def get_legacy_usage_count():
    """Get current legacy usage count."""
    return _LEGACY_CALL_COUNT

warn(
    "Slot6: 'multicultural_truth_synthesis' is deprecated; use 'engine.CulturalSynthesisEngine' and 'adapter.CulturalSynthesisAdapter' instead.",
    DeprecationWarning,
    stacklevel=2,
)


class ProfileWrapper(Mapping[str, Any]):
    """Dict-like view with attribute access for legacy callers."""
    __slots__ = ("_data",)

    def __init__(self, data: Dict[str, Any]):
        # Never mutate the source; shallow copy is enough for our metrics dicts
        self._data = dict(data)

        # Only supply defaults if missing (conservative approach)
        self._data.setdefault("adaptation_effectiveness", 0.0)
        self._data.setdefault("principle_preservation_score", 0.0)
        self._data.setdefault("residual_risk", 1.0)

    # --- Mapping interface ---
    def __getitem__(self, k: str) -> Any:
        return self._data[k]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    # Legacy helpers
    def get(self, k: str, default=None):
        return self._data.get(k, default)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)

    # --- Attribute access ---
    def __getattr__(self, name: str) -> Any:
        try:
            return self._data[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def __repr__(self) -> str:
        return f"ProfileWrapper({self._data!r})"


class AdaptiveSynthesisEngine(CulturalSynthesisEngine):
    """Deprecated alias for CulturalSynthesisEngine."""
    pass


class MulticulturalTruthSynthesisAdapter(CulturalSynthesisAdapter):
    """Deprecated alias for CulturalSynthesisAdapter with ProfileWrapper compatibility."""

    def analyze_cultural_context(
        self,
        institution_name: str,
        ctx: Optional[Dict[str, Any]] = None,
        slot2_result=None,
    ) -> ProfileWrapper:
        """Legacy wrapper that returns ProfileWrapper for CI compatibility."""
        _increment_legacy_usage()  # Track usage for retirement metrics

        # Call parent method to get normal dict result
        data: CulturalProfile = dict(ctx or {})
        data["institution"] = institution_name
        try:
            result = self.engine.synthesize(data)
            return ProfileWrapper(result)
        except Exception:
            profile = CulturalProfile()
            return ProfileWrapper(profile)


class MulticulturalTruthSynthesis(CulturalSynthesisEngine):
    """Deprecated alias for CulturalSynthesisEngine."""
    pass


__all__ = ["AdaptiveSynthesisEngine", "MulticulturalTruthSynthesisAdapter", "MulticulturalTruthSynthesis", "ProfileWrapper"]
