import os
from typing import Dict, Any

import jwt

# SECURITY: JWT_SECRET must be set in environment - no insecure defaults
JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError(
        "CRITICAL: JWT_SECRET environment variable must be set.\n"
        "Generate a secure secret:\n"
        "  python -c 'import secrets; print(secrets.token_hex(32))'\n"
        "Then set: export JWT_SECRET=<generated-value>"
    )

# Validate secret strength (minimum 32 characters)
if len(JWT_SECRET) < 32:
    raise RuntimeError(
        f"CRITICAL: JWT_SECRET must be at least 32 characters long.\n"
        f"Your secret is only {len(JWT_SECRET)} characters.\n"
        f"Generate a secure secret: python -c 'import secrets; print(secrets.token_hex(32))'"
    )

JWT_ALGORITHM = "HS256"

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify a JWT token and return the decoded payload.

    Raises:
        PyJWTError: If the token is invalid or expired.
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
