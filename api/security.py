"""Security utilities for NOVA API endpoints."""

import os
from typing import Optional
from fastapi import HTTPException, Header


def get_api_key() -> str:
    """Get API key from environment with validation."""
    api_key = os.getenv("NOVA_API_KEY")
    if not api_key:
        raise RuntimeError(
            "NOVA_API_KEY not set. Set environment variable for production deployment."
        )
    if api_key in ("default", "changeme", "development", "test"):
        raise RuntimeError(
            "NOVA_API_KEY is set to default value. Use secure key for production."
        )
    return api_key


async def verify_api_key(nova_api_key: Optional[str] = Header(None)) -> str:
    """Verify API key from request header."""
    expected_key = get_api_key()
    
    if not nova_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing NOVA-API-KEY header"
        )
    
    if nova_api_key != expected_key:
        raise HTTPException(
            status_code=403, 
            detail="Invalid API key"
        )
    
    return nova_api_key


def validate_startup_security():
    """Validate security configuration on startup."""
    try:
        api_key = get_api_key()
        if len(api_key) < 32:
            raise RuntimeError("NOVA_API_KEY too short. Use at least 32 characters.")
        print(f"✅ Security: API key configured ({len(api_key)} chars)")
        return True
    except RuntimeError as e:
        print(f"⚠️ Security warning: {e}")
        if os.getenv("NOVA_REQUIRE_SECURITY", "1").strip() == "1":
            raise
        return False
