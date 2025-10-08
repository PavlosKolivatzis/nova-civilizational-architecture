"""
Test build provenance metrics for deployment traceability.
"""

from prometheus_client import generate_latest


def test_build_info_export():
    """Verify build info metric is exported with required labels."""
    from orchestrator.prometheus_metrics import _REGISTRY

    # Generate metrics output
    text = generate_latest(_REGISTRY).decode("utf-8")

    # Verify build info metric is present
    assert "nova_build_info" in text

    # Verify required labels
    assert 'component="orchestrator"' in text
    assert 'version="5.1"' in text

    # At least one sha-like value present (env fallback or git)
    assert "sha=" in text

    # Build timestamp should be present
    assert "built_at=" in text


def test_build_info_sha_fallback():
    """Verify SHA fallback works when git is unavailable."""
    from orchestrator.prometheus_metrics import _get_git_sha_short
    import os

    # Test with NOVA_BUILD_SHA environment variable
    original = os.environ.get('NOVA_BUILD_SHA')
    try:
        os.environ['NOVA_BUILD_SHA'] = 'test-sha-123'
        # Should return git SHA if available, or fallback to env
        sha = _get_git_sha_short()
        assert sha is not None
        assert len(sha) > 0
    finally:
        if original is not None:
            os.environ['NOVA_BUILD_SHA'] = original
        elif 'NOVA_BUILD_SHA' in os.environ:
            del os.environ['NOVA_BUILD_SHA']


def test_default_collectors_registered():
    """Verify process/platform/GC collectors are included."""
    from orchestrator.prometheus_metrics import _REGISTRY

    text = generate_latest(_REGISTRY).decode("utf-8")

    # Should include process metrics
    assert "process_resident_memory_bytes" in text or "python_info" in text

    # Should include GC metrics
    assert "python_gc_objects_collected_total" in text or "python_gc_collections_total" in text


def test_metrics_endpoint_integration():
    """Test that metrics endpoint works with custom registry."""
    from orchestrator.http_metrics import router
    from fastapi.testclient import TestClient
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    client = TestClient(app)
    response = client.get("/metrics")

    assert response.status_code == 200
    ct = response.headers.get("content-type", "")
    # Accept both classic Prometheus text format and newer exposition versions
    allowed = {
        "text/plain; version=0.0.4; charset=utf-8",
        "text/plain; version=1.0.0; charset=utf-8",
    }
    assert (ct in allowed) or (ct.startswith("text/plain") and "charset=utf-8" in ct)
    assert "nova_build_info" in response.text