# ruff: noqa: E402
import os
import sys

# SECURITY: Set JWT_SECRET before any imports (required for nova.auth validation)
# Tests use a known secret - production MUST use a secure random secret
if "JWT_SECRET" not in os.environ:
    # 32+ character test secret (meets security requirement)
    os.environ["JWT_SECRET"] = "test-secret-minimum-32-characters-long-for-security-validation"

# TESTING: Disable rate limiting for tests (allows rapid endpoint calls)
# Production uses NOVA_RATE_LIMITING_ENABLED=1 by default
if "NOVA_RATE_LIMITING_ENABLED" not in os.environ:
    os.environ["NOVA_RATE_LIMITING_ENABLED"] = "0"

import pytest
import jwt

from src_bootstrap import ensure_src_on_path

# Ensure repository root is importable
sys.path.insert(0, os.path.abspath('.'))
ensure_src_on_path()

from nova.auth import JWT_SECRET


@pytest.fixture
def auth_header():
    token = jwt.encode({"sub": "test"}, JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}
