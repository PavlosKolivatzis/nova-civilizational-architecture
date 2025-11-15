"""
REST API endpoints for ledger checkpoints.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .checkpoint_service import CheckpointService
from .checkpoint_types import Checkpoint


router = APIRouter(prefix="/ledger/checkpoints", tags=["ledger-checkpoints"])


class CreateReq(BaseModel):
    anchor_id: str
    start_rid: str
    end_rid: str


class VerifyReq(BaseModel):
    anchor_id: str
    start_rid: str
    end_rid: str
    merkle_root: str


def get_service() -> CheckpointService:
    """Dependency injection for CheckpointService."""
    # Placeholder - in real implementation, this would come from DI container
    from .store import LedgerStore
    from .checkpoint_signer import CheckpointSigner
    store = LedgerStore()
    signer = CheckpointSigner(store)
    return CheckpointService(store, signer)


@router.post("/")
async def create_checkpoint(req: CreateReq, svc: CheckpointService = Depends(get_service)):
    """
    Create and sign a checkpoint for an anchor range.

    POST /ledger/checkpoints
    Body: {"anchor_id": "...", "start_rid": "...", "end_rid": "..."}
    """
    try:
        cp = await svc.create(req.anchor_id, req.start_rid, req.end_rid)
        if cp is None:
            return JSONResponse({"error": "No records in range"}, status_code=400)
        return {"id": cp.id, "merkle_root": cp.merkle_root, "key_id": cp.key_id}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get("/{anchor_id}")
async def get_checkpoint(anchor_id: str, svc: CheckpointService = Depends(get_service)):
    """
    Get the last checkpoint for an anchor.

    GET /ledger/checkpoints/{anchor_id}
    """
    cp = await svc.get_last(anchor_id)
    if not cp:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": cp.id, "merkle_root": cp.merkle_root, "key_id": cp.key_id}


@router.post("/verify")
async def verify(req: VerifyReq, svc: CheckpointService = Depends(get_service)):
    """
    Verify a checkpoint range.

    POST /ledger/checkpoints/verify
    Body: {"anchor_id": "...", "start_rid": "...", "end_rid": "...", "merkle_root": "..."}
    """
    ok, err = await svc.verify_range(req.anchor_id, req.start_rid, req.end_rid, req.merkle_root)
    return {"ok": bool(ok)} if ok else {"ok": False, "error": err or "verification failed"}


def create_checkpoint_router(_service: CheckpointService) -> APIRouter:
    """
    Create checkpoint API router with service dependency.

    Args:
        _service: CheckpointService instance (currently unused, reserved for future use)

    Returns:
        FastAPI router
    """
    return router


# Export the router for direct use
checkpoint_router = router
