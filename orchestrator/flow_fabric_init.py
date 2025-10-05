"""
Flow Fabric Initialization - Register Known Contract Links

Initializes the adaptive link registry with known Nova contracts to establish
baseline flow fabric connectivity. This resolves the "no_links" status by
registering the expected inter-slot contract relationships.
"""

import logging
import os
import yaml
from typing import Dict, Any, List
from .adaptive_connections import adaptive_link_registry, AdaptiveLinkConfig

logger = logging.getLogger(__name__)

# Known Nova contracts from slot map and documentation
KNOWN_CONTRACTS = [
    "TRI_REPORT@1",           # Slot 4 → Slot 2, 5 (Truth Resonance Index)
    "EMOTION_REPORT@1",       # Slot 3 → Slot 6 (Emotional Analysis)
    "CULTURAL_PROFILE@1",     # Slot 6 → Slot 2, 10 (Cultural Synthesis)
    "DETECTION_REPORT@1",     # Slot 2 → Slot 5, 9 (Delta Threshold Detection)
    "CONSTELLATION_REPORT@1", # Slot 5 → Slot 9 (Pattern Mapping)
    "DELTA_THREAT@1",         # Slot 2 → Slot 3 (Threat Assessment)
    "PRODUCTION_CONTROL@1",   # Slot 3 → Slot 7 (Circuit Breaking)
    "META_LENS_REPORT@1",     # Slot 2 → Various (Meta Analysis)
    "CONSTELLATION_STATE@1",  # Slot 5 internal state
    # SIGNALS@1 removed - legacy contract, no producer/consumer (DEF-028)
]

def load_adaptive_links_config() -> Dict[str, Any]:
    """Load adaptive links configuration from YAML file."""
    config_path = os.path.join("config", "adaptive_links.yaml")

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded adaptive links config from {config_path}")
        return config
    except FileNotFoundError:
        logger.warning(f"Adaptive links config not found at {config_path}, using defaults")
        return {}
    except Exception as e:
        logger.error(f"Error loading adaptive links config: {e}")
        return {}

def create_adaptive_link_config(contract_name: str, config_data: Dict[str, Any]) -> AdaptiveLinkConfig:
    """Create AdaptiveLinkConfig from YAML configuration."""
    default_config = config_data.get("default_config", {})
    contract_config = config_data.get("contracts", {}).get(contract_name, {})

    # Merge default and contract-specific configuration
    merged_config = {**default_config, **contract_config}

    return AdaptiveLinkConfig(
        base_weight=merged_config.get("base_weight", 1.0),
        base_frequency=merged_config.get("base_frequency", 1.0),
        min_weight=merged_config.get("min_weight", 0.1),
        max_weight=merged_config.get("max_weight", 3.0),
        min_frequency=merged_config.get("min_frequency", 0.1),
        max_frequency=merged_config.get("max_frequency", 5.0),
        throttle_window_seconds=merged_config.get("throttle_window_seconds", 60),
        history_size=merged_config.get("history_size", 100),
        adaptation_enabled=config_data.get("adaptive_connections_enabled", False)
    )

def initialize_flow_fabric() -> None:
    """Initialize flow fabric with known Nova contracts."""
    logger.info("Initializing Flow Fabric with known contract links...")

    # Load configuration
    config_data = load_adaptive_links_config()

    # Check global feature flags
    adaptive_enabled = config_data.get("adaptive_connections_enabled", False)
    flow_metrics_enabled = config_data.get("flow_metrics_enabled", True)

    # Override from environment variables
    adaptive_enabled = os.getenv("NOVA_ADAPTIVE_CONNECTIONS_ENABLED", str(adaptive_enabled)).lower() == "true"
    flow_metrics_enabled = os.getenv("NOVA_FLOW_METRICS_ENABLED", str(flow_metrics_enabled)).lower() == "true"

    logger.info(f"Flow Fabric initialization: adaptive_enabled={adaptive_enabled}, metrics_enabled={flow_metrics_enabled}")

    if not flow_metrics_enabled:
        logger.warning("Flow metrics disabled - flow fabric will show as unavailable")
        return

    # Register known contracts as adaptive links
    registered_count = 0
    for contract_name in KNOWN_CONTRACTS:
        try:
            link_config = create_adaptive_link_config(contract_name, config_data)
            link = adaptive_link_registry.get_link(contract_name, link_config)
            registered_count += 1
            logger.debug(f"Registered adaptive link: {contract_name} (adaptation_enabled={link_config.adaptation_enabled})")
        except Exception as e:
            logger.error(f"Failed to register adaptive link {contract_name}: {e}")

    logger.info(f"Flow Fabric initialized with {registered_count}/{len(KNOWN_CONTRACTS)} contract links")

    # Log current state
    all_metrics = adaptive_link_registry.get_all_metrics()
    if all_metrics:
        logger.info(f"Active adaptive links: {[m['contract_name'] for m in all_metrics]}")
    else:
        logger.warning("No adaptive links registered - flow fabric will show 'no_links' status")

def get_flow_fabric_status() -> Dict[str, Any]:
    """Get current flow fabric status for diagnostics."""
    all_metrics = adaptive_link_registry.get_all_metrics()

    return {
        "initialized": len(all_metrics) > 0,
        "total_links": len(all_metrics),
        "contracts_registered": [m["contract_name"] for m in all_metrics],
        "adaptation_enabled_count": sum(1 for m in all_metrics if m["adaptation_enabled"]),
        "known_contracts": KNOWN_CONTRACTS,
        "registration_coverage": f"{len(all_metrics)}/{len(KNOWN_CONTRACTS)}"
    }

# Auto-initialize if imported (can be disabled by setting NOVA_FLOW_FABRIC_LAZY_INIT=1)
if __name__ != "__main__" and os.getenv("NOVA_FLOW_FABRIC_LAZY_INIT", "1") == "0":
    try:
        initialize_flow_fabric()
    except Exception as e:
        logger.error(f"Flow Fabric auto-initialization failed: {e}")