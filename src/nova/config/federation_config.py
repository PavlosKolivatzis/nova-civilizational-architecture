"""Federation configuration loader."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass
class PeerEntry:
    id: str
    url: str
    pubkey: str
    enabled: bool = True


@dataclass
class FederationConfig:
    enabled: bool = False
    bind: str = "0.0.0.0:9414"
    registry_path: Optional[Path] = None
    peers: List[PeerEntry] = field(default_factory=list)


def load_registry(path: Path) -> List[PeerEntry]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    peers = []
    for raw in data.get("federation", {}).get("peers", []):
        peers.append(
            PeerEntry(
                id=str(raw["id"]),
                url=str(raw["url"]),
                pubkey=str(raw["pubkey"]),
                enabled=bool(raw.get("enabled", True)),
            )
        )
    return peers


def load_federation_config() -> FederationConfig:
    enabled = os.getenv("FEDERATION_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
    bind = os.getenv("FEDERATION_BIND", "0.0.0.0:9414")
    registry_env = os.getenv("NOVA_FEDERATION_REGISTRY")
    config = FederationConfig(enabled=enabled, bind=bind)
    if registry_env:
        registry_path = Path(registry_env)
        if registry_path.exists():
            config.registry_path = registry_path
            config.peers = load_registry(registry_path)
    return config


__all__ = ["FederationConfig", "PeerEntry", "load_federation_config", "load_registry"]
