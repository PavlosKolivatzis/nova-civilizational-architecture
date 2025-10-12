# ruff: noqa: E402
import os
import sys

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
