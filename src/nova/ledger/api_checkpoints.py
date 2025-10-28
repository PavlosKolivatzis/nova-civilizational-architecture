"""
REST API endpoints for ledger checkpoints.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .checkpoint_service import CheckpointService
from .checkpoint_signer import Checkpoint


router = APIRouter(prefix="/ledger/checkpoints", tags=["ledger-checkpoints"])


class CheckpointResponse(BaseModel):
    """API response for checkpoint data."""
    cid: str
    merkle_root_hex: str
    range_start: str
    range_end: str
    records: int
    algo: str
    version: str
    sig_b64: str
    pubkey_id: str
    created_at: Optional[str]


class RollRequest(BaseModel):
    """Request to roll a new checkpoint."""
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None


def create_checkpoint_router(service: CheckpointService) -> APIRouter:
    """
    Create checkpoint API router with service dependency.

    Args:
        service: CheckpointService instance

    Returns:
        FastAPI router
    """

    @router.post("/roll", response_model=CheckpointResponse)
    async def roll_checkpoint(request: RollRequest):
        """
        Create a new checkpoint.

        POST /ledger/checkpoints/roll
        {
            "start_ts": "2025-10-28T10:00:00Z",  // optional
            "end_ts": "2025-10-28T11:00:00Z"     // optional
        }
        """
        try:
            checkpoint = await service.roll_once(
                start_ts=request.start_ts,
                end_ts=request.end_ts
            )

            return CheckpointResponse(
                cid=checkpoint.cid,
                merkle_root_hex=checkpoint.merkle_root_hex,
                range_start=checkpoint.range_start,
                range_end=checkpoint.range_end,
                records=checkpoint.records,
                algo=checkpoint.algo,
                version=checkpoint.version,
                sig_b64=checkpoint.sig_b64,
                pubkey_id=checkpoint.pubkey_id,
                created_at=checkpoint.created_at.isoformat() if checkpoint.created_at else None
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create checkpoint: {e}")

    @router.get("/latest", response_model=CheckpointResponse)
    async def get_latest_checkpoint():
        """
        Get the most recent checkpoint.

        GET /ledger/checkpoints/latest
        """
        try:
            checkpoint = await service.signer.store.get_latest_checkpoint()
            if not checkpoint:
                raise HTTPException(status_code=404, detail="No checkpoints found")

            return CheckpointResponse(
                cid=checkpoint.cid,
                merkle_root_hex=checkpoint.merkle_root,
                range_start=checkpoint.range_start,
                range_end=checkpoint.range_end,
                records=checkpoint.record_count,
                algo="sha3-256",  # Default
                version="cp-1.0",  # Default
                sig_b64=checkpoint.sig or "",
                pubkey_id="",  # Not stored in legacy checkpoints
                created_at=checkpoint.created_at.isoformat() if checkpoint.created_at else None
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get latest checkpoint: {e}")

    @router.get("/{cid}", response_model=CheckpointResponse)
    async def get_checkpoint(cid: str):
        """
        Get checkpoint by ID.

        GET /ledger/checkpoints/{cid}
        """
        try:
            checkpoint = await service.signer.store.get_checkpoint(cid)
            if not checkpoint:
                raise HTTPException(status_code=404, detail=f"Checkpoint {cid} not found")

            return CheckpointResponse(
                cid=checkpoint.cid,
                merkle_root_hex=checkpoint.merkle_root,
                range_start=checkpoint.range_start,
                range_end=checkpoint.range_end,
                records=checkpoint.record_count,
                algo="sha3-256",
                version="cp-1.0",
                sig_b64=checkpoint.sig or "",
                pubkey_id="",
                created_at=checkpoint.created_at.isoformat() if checkpoint.created_at else None
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get checkpoint {cid}: {e}")

    @router.post("/{cid}/verify")
    async def verify_checkpoint(cid: str):
        """
        Verify checkpoint signature and Merkle root.

        POST /ledger/checkpoints/{cid}/verify
        Returns: {"valid": true, "error": "..."}
        """
        try:
            checkpoint = await service.signer.store.get_checkpoint(cid)
            if not checkpoint:
                raise HTTPException(status_code=404, detail=f"Checkpoint {cid} not found")

            # Convert to new Checkpoint format for verification
            cp = Checkpoint(
                cid=checkpoint.cid,
                merkle_root_hex=checkpoint.merkle_root,
                range_start=checkpoint.range_start,
                range_end=checkpoint.range_end,
                records=checkpoint.record_count,
                sig_b64=checkpoint.sig or "",
                pubkey_id="",  # Legacy checkpoints don't have pubkey_id
                created_at=checkpoint.created_at
            )

            is_valid, error = await service.signer.verify_range(cp)

            return {
                "valid": is_valid,
                "error": error if not is_valid else "",
                "checkpoint": {
                    "cid": cp.cid,
                    "merkle_root_hex": cp.merkle_root_hex,
                    "records": cp.records
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to verify checkpoint {cid}: {e}")

    return router


# Export the router for direct use
checkpoint_router = router