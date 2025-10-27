"""
Autonomous Verification Ledger (AVL) - Phase 13

Hash-linked, append-only ledger for cross-slot trust provenance.
Unifies PQC attestations, fidelity signals, and verification results.
"""

from .model import LedgerRecord, Checkpoint, RecordKind

__all__ = ["LedgerRecord", "Checkpoint", "RecordKind"]
