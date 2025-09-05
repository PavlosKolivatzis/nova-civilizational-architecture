from pathlib import Path

import pytest
import yaml

from slots.slot02_deltathresh.enhanced.config import (
    EnhancedProcessingConfig,
    LogLevel,
    OperationalMode,
)
from slots.slot02_deltathresh.enhanced.config_manager import ConfigManager


def test_from_environment(monkeypatch):
    monkeypatch.setenv("OPERATIONAL_MODE", "pass_through")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    cfg = EnhancedProcessingConfig.from_environment()
    assert cfg.operational_mode is OperationalMode.PASS_THROUGH
    assert cfg.logging.level is LogLevel.DEBUG


def test_config_manager_load(tmp_path: Path, monkeypatch):
    data = {
        "operational_mode": "pass_through",
        "logging": {"level": "ERROR"},
        "security": {"enable_authentication": False},
    }
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.dump(data))

    monkeypatch.setenv("JWT_SECRET", "secret")
    mgr = ConfigManager()
    assert mgr.config.operational_mode is OperationalMode.STABLE_LOCK
    mgr.load_from_file(path)
    assert mgr.config.operational_mode is OperationalMode.PASS_THROUGH
    assert mgr.config.logging.level is LogLevel.ERROR


def test_config_manager_requires_valid_initial_config(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    cfg = EnhancedProcessingConfig()
    with pytest.raises(ValueError):
        ConfigManager(cfg)
