"""Trust model scaffold tests."""

from __future__ import annotations

import pytest

from nova.federation.trust_model import score_trust


@pytest.mark.health
def test_score_trust_true_false():
    assert score_trust(True) == {"verified": True, "score": 1.0}
    assert score_trust(False) == {"verified": False, "score": 0.0}
