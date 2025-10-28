"""
Autonomous Verification Ledger (AVL) - Phase 13/14

Hash-linked, append-only ledger for cross-slot trust provenance.
Unifies PQC attestations, fidelity signals, and verification results.

Phase 14-1: PostgreSQL persistence backend.
"""

from .model import LedgerRecord, Checkpoint, RecordKind
from .store import LedgerStore

__all__ = ["LedgerRecord", "Checkpoint", "RecordKind", "LedgerStore"]
