import os
import sys

import pytest
import jwt

from auth import JWT_SECRET

# Ensure repository root is importable
sys.path.insert(0, os.path.abspath('.'))


@pytest.fixture
def auth_header():
    token = jwt.encode({"sub": "test"}, JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}
