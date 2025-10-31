"""Federation scaffolding package (Phase 15-1)."""

from .peer_registry import PeerRegistry
from .trust_model import score_trust

__all__ = ["PeerRegistry", "score_trust"]
