"""
REST API endpoints for ledger checkpoints.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .checkpoint_service import CheckpointService
from .checkpoint_types import Checkpoint


router = APIRouter(prefix="/ledger/checkpoints", tags=["ledger-checkpoints"])


class CheckpointResponse(BaseModel):
    """API response for checkpoint data."""
    id: str
    anchor_id: str
    merkle_root: str
    start_rid: str
    end_rid: str
    prev_root: Optional[str]
    ts: str
    sig: Optional[str]
    key_id: Optional[str]
    version: str


# RollRequest removed - using anchor-based checkpoint creation


def create_checkpoint_router(service: CheckpointService) -> APIRouter:
    """
    Create checkpoint API router with service dependency.

    Args:
        service: CheckpointService instance

    Returns:
        FastAPI router
    """

    @router.post("/{anchor_id}")
    async def create_checkpoint(anchor_id: str):
        """
        Create and sign a checkpoint for an anchor.

        POST /ledger/checkpoints/{anchor_id}
        """
        try:
            checkpoint = await service.create_and_sign(anchor_id)
            return {"checkpoint": checkpoint.to_dict()}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error: {e}")

    @router.get("/{checkpoint_id}")
    async def get_checkpoint(checkpoint_id: str):
        """
        Get checkpoint by ID.

        GET /ledger/checkpoints/{checkpoint_id}
        """
        try:
            checkpoint = await service.store.fetch_checkpoint(checkpoint_id)
            if not checkpoint:
                raise HTTPException(status_code=404, detail=f"Checkpoint {checkpoint_id} not found")

            return {"checkpoint": checkpoint.to_dict()}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get checkpoint {checkpoint_id}: {e}")

    @router.get("/{checkpoint_id}/verify")
    async def verify_checkpoint(checkpoint_id: str):
        """
        Verify a checkpoint by ID.

        GET /ledger/checkpoints/{checkpoint_id}/verify
        Returns: {"valid": true}
        """
        try:
            is_valid = await service.verify(checkpoint_id)
            return {"valid": is_valid}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Verification error: {e}")

    return router


# Export the router for direct use
checkpoint_router = router