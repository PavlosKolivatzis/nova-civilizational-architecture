"""
Autonomous Verification Ledger (AVL) - Phase 13/14

Hash-linked, append-only ledger for cross-slot trust provenance.
Unifies PQC attestations, fidelity signals, and verification results.

Phase 14-1: PostgreSQL persistence backend.
Phase 14-2: Merkle checkpoints + PQC signer.
"""

from .model import LedgerRecord, Checkpoint, RecordKind
# Do NOT import store here to avoid side-effects (metrics, DB setup, circular imports)
# from .store import LedgerStore

__all__ = ["LedgerRecord", "Checkpoint", "RecordKind"]
