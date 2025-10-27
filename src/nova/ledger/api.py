"""
REST API for Autonomous Verification Ledger.

Phase 13 RUN 13-2: Endpoints for append, query, and verification.
"""

from __future__ import annotations

from typing import Optional
from flask import Blueprint, request, jsonify
import logging

from .store import LedgerStore
from .verify import ChainVerifier
from .model import RecordKind

# Create Flask blueprint
ledger_bp = Blueprint("ledger", __name__, url_prefix="/ledger")

# Global instances (will be initialized by app)
_store: Optional[LedgerStore] = None
_verifier: Optional[ChainVerifier] = None
_logger: Optional[logging.Logger] = None


def init_ledger_api(
    store: Optional[LedgerStore] = None,
    verifier: Optional[ChainVerifier] = None,
    logger: Optional[logging.Logger] = None,
):
    """Initialize ledger API with store and verifier instances."""
    global _store, _verifier, _logger
    _store = store or LedgerStore()
    _verifier = verifier or ChainVerifier()
    _logger = logger or logging.getLogger("ledger.api")


@ledger_bp.route("/append", methods=["POST"])
def append_record():
    """
    Append a new record to the ledger.

    POST /ledger/append
    {
      "anchor_id": "...",
      "slot": "01",
      "kind": "PQC_SIGNED",
      "payload": {...},
      "producer": "slot01",
      "version": "1.0.0",
      "sig": null  // optional base64 PQC signature
    }

    Returns:
      201 Created with record details
      400 Bad Request if validation fails
      500 Internal Server Error if append fails
    """
    if not _store:
        return jsonify({"error": "Ledger not initialized"}), 500

    try:
        data = request.get_json()

        # Validate required fields
        required = ["anchor_id", "slot", "kind", "payload"]
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({"error": f"Missing required fields: {missing}"}), 400

        # Convert kind to enum
        try:
            kind = RecordKind(data["kind"])
        except ValueError:
            return jsonify({"error": f"Invalid kind: {data['kind']}"}), 400

        # Append record
        record = _store.append(
            anchor_id=data["anchor_id"],
            slot=data["slot"],
            kind=kind,
            payload=data["payload"],
            producer=data.get("producer", "unknown"),
            version=data.get("version", "unknown"),
            sig=data.get("sig"),  # TODO: Decode base64 if present
        )

        return (
            jsonify(
                {
                    "rid": record.rid,
                    "anchor_id": record.anchor_id,
                    "hash": record.hash,
                    "prev_hash": record.prev_hash,
                    "ts": record.ts.isoformat(),
                }
            ),
            201,
        )

    except Exception as e:
        _logger.error(f"Failed to append record: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@ledger_bp.route("/chain/<anchor_id>", methods=["GET"])
def get_chain(anchor_id: str):
    """
    Get all records for an anchor in chronological order.

    GET /ledger/chain/{anchor_id}?limit=100

    Returns:
      200 OK with list of records
      404 Not Found if no records exist for anchor
    """
    if not _store:
        return jsonify({"error": "Ledger not initialized"}), 500

    try:
        limit = request.args.get("limit", 100, type=int)
        records = _store.get_chain(anchor_id)

        if not records:
            return jsonify({"error": f"No records found for anchor {anchor_id}"}), 404

        # Limit results
        records = records[:limit]

        return jsonify(
            {
                "anchor_id": anchor_id,
                "records": len(records),
                "chain": [
                    {
                        "rid": r.rid,
                        "slot": r.slot,
                        "kind": r.kind.value if isinstance(r.kind, RecordKind) else r.kind,
                        "ts": r.ts.isoformat(),
                        "hash": r.hash,
                        "prev_hash": r.prev_hash,
                        "payload": r.payload,
                    }
                    for r in records
                ],
            }
        )

    except Exception as e:
        _logger.error(f"Failed to get chain: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@ledger_bp.route("/verify/<anchor_id>", methods=["POST"])
def verify_anchor(anchor_id: str):
    """
    Verify ledger chain and compute trust score for an anchor.

    POST /ledger/verify/{anchor_id}

    Returns:
      200 OK with verification result and trust score
      404 Not Found if no records exist for anchor
      500 Internal Server Error if verification fails
    """
    if not _store or not _verifier:
        return jsonify({"error": "Ledger not initialized"}), 500

    try:
        records = _store.get_chain(anchor_id)

        if not records:
            return jsonify({"error": f"No records found for anchor {anchor_id}"}), 404

        # Verify chain
        result = _verifier.verify_chain(records)

        return jsonify(result.to_dict())

    except Exception as e:
        _logger.error(f"Failed to verify chain: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@ledger_bp.route("/stats", methods=["GET"])
def get_stats():
    """
    Get ledger statistics.

    GET /ledger/stats

    Returns:
      200 OK with ledger stats
    """
    if not _store:
        return jsonify({"error": "Ledger not initialized"}), 500

    try:
        stats = _store.get_stats()
        return jsonify(stats)

    except Exception as e:
        _logger.error(f"Failed to get stats: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
