import pytest

@pytest.mark.skip(reason="Phase 1 skeleton; enable when ASGI lifespan is wired")
def test_app_lifespan_startup_shutdown():
    assert True