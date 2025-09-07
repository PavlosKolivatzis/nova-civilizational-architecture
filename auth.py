import os
from typing import Dict, Any

import jwt
from jwt import PyJWTError

JWT_SECRET = os.environ.get("JWT_SECRET", "testing-secret")
JWT_ALGORITHM = "HS256"

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify a JWT token and return the decoded payload.

    Raises:
        PyJWTError: If the token is invalid or expired.
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
