"""
Ledger store factory for backend selection.

Phase 14-1: PostgreSQL persistence with fallback to memory store.
"""

import logging
from typing import Optional

from .store import LedgerStore
from .store_postgres import PostgresLedgerStore
from ..config.ledger_config import LedgerConfig
from prometheus_client import Counter

# Fallback counter
ledger_persist_fallback_total = Counter(
    "ledger_persist_fallback_total",
    "Ledger fallback to memory store",
    ["reason"]
)


def create_ledger_store(config: Optional[LedgerConfig] = None, logger: Optional[logging.Logger] = None) -> LedgerStore:
    """
    Create a ledger store instance based on configuration.

    Args:
        config: Ledger configuration. If None, loads from environment.
        logger: Optional logger instance.

    Returns:
        LedgerStore instance (memory or PostgreSQL backend).
    """
    if config is None:
        config = LedgerConfig.from_env()

    if logger is None:
        logger = logging.getLogger("ledger.factory")

    if config.backend == "postgres":
        if not config.dsn:
            logger.warning("PostgreSQL DSN not configured, falling back to memory store")
            ledger_persist_fallback_total.labels(reason="no_dsn").inc()
            return LedgerStore(logger=logger)

        try:
            return PostgresLedgerStore(
                dsn=config.dsn,
                pool_size=config.pool_size,
                timeout=config.timeout,
                logger=logger
            )
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL store: {e}, falling back to memory store")
            ledger_persist_fallback_total.labels(reason="connection_failed").inc()
            return LedgerStore(logger=logger)

    elif config.backend == "memory":
        return LedgerStore(logger=logger)

    else:
        logger.warning(f"Unknown ledger backend '{config.backend}', falling back to memory store")
        ledger_persist_fallback_total.labels(reason="unknown_backend").inc()
        return LedgerStore(logger=logger)