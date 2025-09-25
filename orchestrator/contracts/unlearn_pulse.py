"""UNLEARN_PULSE@1 contract definition."""

from typing import Optional
from pydantic import BaseModel, Field
import time


class UnlearnPulseV1(BaseModel):
    """Contract: inform a slot to decay/release context related to a key."""
    schema_id: str = Field(default="UNLEARN_PULSE", frozen=True)
    schema_version: int = Field(default=1, frozen=True)

    key: str                    # e.g., "slot03.phase_lock"
    target_slot: str            # e.g., "slot03"
    published_by: Optional[str] = None  # original publisher (slot id)
    ttl_seconds: Optional[float] = None
    access_count: Optional[int] = None
    age_seconds: Optional[float] = None
    scope: Optional[str] = None         # INTERNAL/PUBLIC/PRIVATE
    reason: str = "ttl_expired"
    ts: float = Field(default_factory=lambda: time.time())