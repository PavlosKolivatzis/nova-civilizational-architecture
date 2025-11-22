"""
Ledger store factory for backend selection.

Phase 14-1: PostgreSQL persistence with fallback to memory store.
"""

import logging
from typing import Optional

from .store import LedgerStore
from .store_postgres import PostgresLedgerStore
from ..config.ledger_config import LedgerConfig

# Lazy import fallback counter to avoid registration at import time
_fallback_counter = None

# Global in-memory store singleton (for test isolation and shared state)
_memory_store_singleton: Optional[LedgerStore] = None

def _get_fallback_counter():
    global _fallback_counter
    if _fallback_counter is None:
        from prometheus_client import Counter, REGISTRY
        try:
            _fallback_counter = Counter(
                "ledger_persist_fallback_total",
                "Ledger fallback to memory store",
                ["reason"]
            )
        except ValueError:
            # Metric already exists, retrieve it from registry
            _fallback_counter = REGISTRY._names_to_collectors["ledger_persist_fallback_total"]
    return _fallback_counter


def create_ledger_store(config: Optional[LedgerConfig] = None, logger: Optional[logging.Logger] = None) -> LedgerStore:
    """
    Create a ledger store instance based on configuration.

    Args:
        config: Ledger configuration. If None, loads from environment.
        logger: Optional logger instance.

    Returns:
        LedgerStore instance (memory or PostgreSQL backend).
    """
    global _memory_store_singleton

    if config is None:
        config = LedgerConfig.from_env()

    if logger is None:
        logger = logging.getLogger("ledger.factory")

    if config.backend == "postgres":
        if not config.dsn:
            logger.warning("PostgreSQL DSN not configured, falling back to memory store")
            _get_fallback_counter().labels(reason="no_dsn").inc()
            if _memory_store_singleton is None:
                _memory_store_singleton = LedgerStore(logger=logger)
            return _memory_store_singleton

        try:
            return PostgresLedgerStore(
                dsn=config.dsn,
                pool_size=config.pool_size,
                timeout=config.timeout,
                logger=logger
            )
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL store: {e}, falling back to memory store")
            _get_fallback_counter().labels(reason="connection_failed").inc()
            if _memory_store_singleton is None:
                _memory_store_singleton = LedgerStore(logger=logger)
            return _memory_store_singleton

    elif config.backend == "memory":
        if _memory_store_singleton is None:
            _memory_store_singleton = LedgerStore(logger=logger)
        return _memory_store_singleton

    else:
        logger.warning(f"Unknown ledger backend '{config.backend}', falling back to memory store")
        _get_fallback_counter().labels(reason="unknown_backend").inc()
        if _memory_store_singleton is None:
            _memory_store_singleton = LedgerStore(logger=logger)
        return _memory_store_singleton
