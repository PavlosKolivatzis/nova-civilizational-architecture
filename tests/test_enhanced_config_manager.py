import asyncio
import threading
import time
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio
import yaml

from slots.config.enhanced_manager import (
    EnhancedConfigManager,
    get_config_manager,
    get_slot_config,
)


class TestEnhancedConfigManager:
    """Test suite for production-hardened config manager."""

    @pytest_asyncio.fixture
    async def temp_config_dir(self):
        """Create temporary config directory with test slots."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "slots"
            slot2_dir = config_dir / "slot02_deltathresh"
            slot2_dir.mkdir(parents=True)

            slot2_meta = {
                "slot": 2,
                "name": "ΔTHRESH Integration Manager",
                "version": "2.0.0",
                "entry_point": "slots/slot02_deltathresh/core.py:DeltaThreshProcessor",
                "config_schema": {
                    "truth_threshold": "float",
                    "tri_enabled": "bool",
                },
                "runtime_constraints": {"max_processing_time_ms": 50},
            }

            meta_name = f"{slot2_dir.name}.meta.yaml"
            with open(slot2_dir / meta_name, "w", encoding="utf-8") as f:
                yaml.dump(slot2_meta, f)

            yield str(config_dir)

    @pytest.mark.asyncio
    async def test_initialization_without_watchdog(self, temp_config_dir):
        """Test initialization works without watchdog dependency."""
        with patch("slots.config.enhanced_manager._WATCHDOG", False):
            manager = EnhancedConfigManager(config_dir=temp_config_dir)
            await manager.initialize()

            assert len(manager.slot_metadata) == 1
            assert 2 in manager.slot_metadata
            assert manager.slot_metadata[2].name == "ΔTHRESH Integration Manager"

            await manager.shutdown()

    @pytest.mark.asyncio
    async def test_polling_watcher_fallback(self, temp_config_dir):
        """Test polling fallback when watchdog unavailable."""
        with patch("slots.config.enhanced_manager._WATCHDOG", False):
            manager = EnhancedConfigManager(
                config_dir=temp_config_dir, enable_hot_reload=True
            )
            await manager.initialize()

            assert manager._poll_thread is not None
            assert manager._poll_thread.is_alive()

            await manager.shutdown()

    @pytest.mark.asyncio
    async def test_env_variable_precedence(self, temp_config_dir):
        """Test environment variable precedence is preserved."""
        with patch.dict(
            "os.environ",
            {"NOVA_SLOT02_truth_threshold": "0.95", "NOVA_SLOT2_tri_enabled": "false"},
        ):
            manager = EnhancedConfigManager(config_dir=temp_config_dir)
            await manager.initialize()

            config = manager.get_slot_config(2)
            assert config["truth_threshold"] == 0.95
            assert config["tri_enabled"] is False

            await manager.shutdown()

    @pytest.mark.asyncio
    async def test_hot_reload_with_polling(self, temp_config_dir):
        """Test hot-reload functionality with polling watcher."""
        with patch("slots.config.enhanced_manager._WATCHDOG", False):
            manager = EnhancedConfigManager(
                config_dir=temp_config_dir, enable_hot_reload=True
            )
            await manager.initialize()

            # Give poller time to record initial state
            await asyncio.sleep(1.2)

            changes_detected = []

            def on_change(slot_id, old_cfg, new_cfg):
                changes_detected.append((slot_id, old_cfg, new_cfg))

            manager.register_config_listener(on_change)

            slot2_dir = Path(temp_config_dir) / "slot02_deltathresh"
            meta_path = slot2_dir / f"{slot2_dir.name}.meta.yaml"
            with open(meta_path, "r", encoding="utf-8") as f:
                meta_data = yaml.safe_load(f)
            meta_data["version"] = "2.1.0"
            with open(meta_path, "w", encoding="utf-8") as f:
                yaml.dump(meta_data, f)

            await asyncio.sleep(1.5)

            assert len(changes_detected) > 0
            slot_id, _old_cfg, new_cfg = changes_detected[0]
            assert slot_id == 2
            assert new_cfg["version"] == "2.1.0"

            await manager.shutdown()

    def test_sync_wrapper_no_loop(self):
        """Test sync wrapper works when no event loop is running."""
        config = get_slot_config(999)
        assert config == {}

    @pytest.mark.asyncio
    async def test_sync_wrapper_with_loop(self):
        """Test sync wrapper works within async context."""
        manager = await get_config_manager()
        config = get_slot_config(2)
        assert isinstance(config, dict)
        await manager.shutdown()

    @pytest.mark.asyncio
    async def test_thread_safety(self, temp_config_dir):
        """Test thread safety of configuration operations."""
        manager = EnhancedConfigManager(config_dir=temp_config_dir)
        await manager.initialize()

        results = []
        exceptions = []

        def worker():
            try:
                for _ in range(10):
                    config = manager.get_slot_config(2)
                    results.append(config.get("slot", None))
                    time.sleep(0.01)
            except Exception as exc:  # pragma: no cover - defensive
                exceptions.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(exceptions) == 0
        assert all(r == 2 for r in results)

        await manager.shutdown()

    @pytest.mark.asyncio
    async def test_graceful_error_handling(self, temp_config_dir):
        """Test graceful handling of various error conditions."""
        manager = EnhancedConfigManager(config_dir=temp_config_dir)
        await manager.initialize()

        config = manager.get_slot_config(999)
        assert config == {}

        invalid_yaml_dir = Path(temp_config_dir) / "slot03_invalid"
        invalid_yaml_dir.mkdir()
        invalid_meta = invalid_yaml_dir / f"{invalid_yaml_dir.name}.meta.yaml"
        with open(invalid_meta, "w", encoding="utf-8") as f:
            f.write("invalid: yaml: content: [")

        await manager._load_all_metadata()
        assert 2 in manager.slot_metadata

        await manager.shutdown()

    @pytest.mark.asyncio
    async def test_listener_exception_handling(self, temp_config_dir):
        """Test that listener exceptions don't break the system."""
        manager = EnhancedConfigManager(config_dir=temp_config_dir)
        await manager.initialize()

        def bad_listener(slot_id, old_cfg, new_cfg):
            raise ValueError("Test exception")

        def good_listener(slot_id, old_cfg, new_cfg):
            good_listener.called = True

        good_listener.called = False
        manager.register_config_listener(bad_listener)
        manager.register_config_listener(good_listener)

        await manager._notify_config_change(2, {}, {"version": "2.1.0"})
        assert good_listener.called

        await manager.shutdown()


@pytest.mark.asyncio
async def test_real_world_scenario():
    """Test a realistic production scenario."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "slots"

        slots_data = {
            2: {
                "slot": 2,
                "name": "ΔTHRESH Integration Manager",
                "version": "2.0.0",
                "entry_point": "slots/slot02_deltathresh/core.py:DeltaThreshProcessor",
                "config_schema": {"truth_threshold": "float"},
            },
            6: {
                "slot": 6,
                "name": "Cultural Synthesis Engine",
                "version": "7.4.1",
                "entry_point": "slots/slot06_cultural_synthesis/adapter.py:Adapter",
            },
            9: {
                "slot": 9,
                "name": "Distortion Protection",
                "version": "2.4.0",
                "entry_point": "slots/slot09_distortion_protection/core.py:Core",
            },
        }

        for slot_id, data in slots_data.items():
            slot_dir = config_dir / f"slot{slot_id:02d}_test"
            slot_dir.mkdir(parents=True)
            meta_name = f"{slot_dir.name}.meta.yaml"
            with open(slot_dir / meta_name, "w", encoding="utf-8") as f:
                yaml.dump(data, f)

        with patch.dict(
            "os.environ",
            {
                "NOVA_SLOT02_truth_threshold": "0.9",
                "NOVA_SLOT06_cultural_weights": '{"test": true}',
                "NOVA_SLOT09_detection_sensitivity": "0.85",
            },
        ):
            with patch("slots.config.enhanced_manager._WATCHDOG", False):
                manager = EnhancedConfigManager(config_dir=str(config_dir))
                await manager.initialize()

                assert set(manager.list_slots()) == {2, 6, 9}

                slot2_config = manager.get_slot_config(2)
                assert slot2_config["truth_threshold"] == 0.9

                changes_detected = []
                manager.register_config_listener(
                    lambda s, o, n: changes_detected.append((s, o, n))
                )

                slot6_meta_path = config_dir / "slot06_test" / "slot06_test.meta.yaml"
                with open(slot6_meta_path, "r", encoding="utf-8") as f:
                    meta = yaml.safe_load(f)
                meta["version"] = "7.5.0"
                with open(slot6_meta_path, "w", encoding="utf-8") as f:
                    yaml.dump(meta, f)

                await manager._handle_config_change(str(slot6_meta_path))
                assert len(changes_detected) == 1
                assert changes_detected[0][0] == 6

                export_data = manager.export_config(6)
                assert export_data["slot_id"] == 6
                assert export_data["metadata"]["version"] == "7.5.0"

                await manager.shutdown()
