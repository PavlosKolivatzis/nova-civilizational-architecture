"""Test singleton metrics guard protection."""
import os
import pytest

@pytest.mark.asyncio
async def test_startup_guard_blocks_multi_worker(monkeypatch):
    """Startup guard must block multi-worker configurations."""
    monkeypatch.setenv("NOVA_REQUIRE_SINGLETON_METRICS", "1")
    monkeypatch.setenv("UVICORN_WORKERS", "2")
    from orchestrator.app import _startup
    with pytest.raises(RuntimeError, match="single-process"):
        await _startup()

@pytest.mark.asyncio
async def test_startup_guard_allows_single_worker(monkeypatch, tmp_path):
    """Startup guard allows single-worker configurations."""
    monkeypatch.setenv("NOVA_REQUIRE_SINGLETON_METRICS", "1")
    monkeypatch.setenv("UVICORN_WORKERS", "1")
    # prevent repo writes
    monkeypatch.setenv("NOVA_UNLEARN_PULSE_PATH", str(tmp_path / "pulses.ndjson"))

    from orchestrator.app import _startup
    await _startup()  # should not raise

@pytest.mark.asyncio
async def test_startup_guard_can_be_disabled(monkeypatch, tmp_path):
    """Guard can be disabled to allow multiprocess metrics (future mode)."""
    monkeypatch.setenv("NOVA_REQUIRE_SINGLETON_METRICS", "0")
    monkeypatch.setenv("UVICORN_WORKERS", "4")
    monkeypatch.setenv("NOVA_UNLEARN_PULSE_PATH", str(tmp_path / "pulses.ndjson"))

    from orchestrator.app import _startup
    await _startup()  # should not raise

def test_startup_guard_environment_detection(monkeypatch):
    """Guard should read worker count from UVICORN_WORKERS or WEB_CONCURRENCY."""
    from orchestrator.app import _startup
    import asyncio

    # Prefer WEB_CONCURRENCY when UVICORN_WORKERS is absent
    monkeypatch.delenv("UVICORN_WORKERS", raising=False)
    monkeypatch.setenv("WEB_CONCURRENCY", "3")
    monkeypatch.setenv("NOVA_REQUIRE_SINGLETON_METRICS", "1")

    async def _run():
        with pytest.raises(RuntimeError, match="workers=3"):
            await _startup()

    asyncio.run(_run())