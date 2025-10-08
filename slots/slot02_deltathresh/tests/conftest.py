# slots/slot02_deltathresh/tests/conftest.py
import sys
import pytest

ENV_KEYS = {
    "NOVA_ENABLE_META_LENS",
    "NOVA_META_LENS_TEST_ENFORCE_REAL",
    "META_LENS_MAX_ITERS",
    "META_LENS_ALPHA",
    "META_LENS_EPSILON",
    "META_LENS_STRICT_VALIDATION",
}

MODULE_KEYS = [
    "slots.slot02_deltathresh.plugin_meta_lens_addition",
    "slots.slot02_deltathresh.meta_lens_processor",
    "slots.slot02_deltathresh.adapter_integration_patch",
]

def _purge_modules():
    for k in MODULE_KEYS:
        if k in sys.modules:
            del sys.modules[k]

@pytest.fixture(autouse=True)
def fresh_meta_lens_env(monkeypatch):
    # 1) Clear env keys before each test
    for k in ENV_KEYS:
        monkeypatch.delenv(k, raising=False)
    # 2) Ensure default OFF unless a test turns it on
    monkeypatch.setenv("NOVA_ENABLE_META_LENS", "0")
    # 3) Purge cached modules so imports see the test's env
    _purge_modules()
    yield
    # 4) Purge again after, to avoid bleed into next test
    _purge_modules()