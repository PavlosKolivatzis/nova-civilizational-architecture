import pytest
import logging

def test_lifespan_disabled_by_default(caplog):
    """Test that lifespan management is disabled by default."""
    pytest.importorskip("fastapi")

    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from lifespan import create_fastapi_lifespan

    caplog.set_level(logging.INFO)
    app = FastAPI(lifespan=create_fastapi_lifespan(scoped=True))

    with TestClient(app) as _:
        pass

    # No example task logs expected when disabled
    assert "Example startup task executed" not in caplog.text
    assert "Example shutdown task executed" not in caplog.text
    assert "Lifespan management disabled" in caplog.text

def test_lifespan_enabled_runs_tasks(monkeypatch, caplog):
    """Test that lifespan management executes tasks when enabled."""
    pytest.importorskip("fastapi")

    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from lifespan import create_fastapi_lifespan, LifespanManager, example_startup_task, example_shutdown_task

    caplog.set_level(logging.INFO)
    monkeypatch.setenv("NOVA_ENABLE_LIFESPAN", "true")

    # Create scoped manager to avoid global state
    mgr = LifespanManager()
    mgr.add_startup_task("example_startup", example_startup_task)
    mgr.add_shutdown_task("example_shutdown", example_shutdown_task)

    app = FastAPI(lifespan=mgr.lifespan_context)

    with TestClient(app) as _:
        pass

    assert "Starting lifespan management" in caplog.text
    assert "Example startup task executed" in caplog.text
    assert "Example shutdown task executed" in caplog.text
    assert "Application startup completed successfully" in caplog.text
    assert "Application shutdown completed" in caplog.text

def test_lifespan_manager_deduplication():
    """Test that duplicate task names are not added."""
    from lifespan import LifespanManager

    async def task1():
        pass

    async def task2():
        pass

    mgr = LifespanManager()

    # Add tasks with same name
    mgr.add_startup_task("duplicate", task1)
    mgr.add_startup_task("duplicate", task2)  # Should be ignored

    assert len(mgr.startup_tasks) == 1
    assert mgr.startup_tasks[0][1] == task1  # First task is kept

def test_lifespan_manager_reset():
    """Test that reset clears all tasks and state."""
    from lifespan import LifespanManager

    async def dummy_task():
        pass

    mgr = LifespanManager()
    mgr.add_startup_task("test", dummy_task)
    mgr.add_shutdown_task("test2", dummy_task)
    mgr.startup_complete = True

    mgr.reset()

    assert len(mgr.startup_tasks) == 0
    assert len(mgr.shutdown_tasks) == 0
    assert len(mgr._names_seen) == 0
    assert mgr.startup_complete is False
    assert mgr.shutdown_complete is False

def test_lifespan_env_variants(monkeypatch, caplog):
    """Test that different environment variable values are accepted."""
    pytest.importorskip("fastapi")

    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from lifespan import create_fastapi_lifespan

    caplog.set_level(logging.INFO)

    # Test different valid values
    for value in ["1", "true", "TRUE", "yes", "YES", "on", "ON"]:
        caplog.clear()
        monkeypatch.setenv("NOVA_ENABLE_LIFESPAN", value)

        app = FastAPI(lifespan=create_fastapi_lifespan(scoped=True))

        with TestClient(app) as _:
            pass

        assert "Starting lifespan management" in caplog.text

    # Test invalid values
    for value in ["0", "false", "no", "off", "invalid", ""]:
        caplog.clear()
        monkeypatch.setenv("NOVA_ENABLE_LIFESPAN", value)

        app = FastAPI(lifespan=create_fastapi_lifespan(scoped=True))

        with TestClient(app) as _:
            pass

        assert "Lifespan management disabled" in caplog.text