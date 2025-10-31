"""Federation scaffolding package (Phase 15-3)."""

from .peer_registry import PeerRegistry
from .trust_model import score_trust
from .sync import RangeSyncer

__all__ = ["PeerRegistry", "score_trust", "RangeSyncer"]
