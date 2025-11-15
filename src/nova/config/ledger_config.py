"""
Ledger configuration for Autonomous Verification Ledger.

Phase 14-1: PostgreSQL Persistence
"""

import os
from dataclasses import dataclass


@dataclass
class LedgerConfig:
    """Configuration for ledger persistence and operations."""

    # Backend selection
    backend: str = "memory"  # "memory" or "postgres"

    # PostgreSQL connection settings
    dsn: str = ""
    pool_size: int = 5
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "LedgerConfig":
        """Load ledger configuration from environment variables."""
        return cls(
            backend=os.getenv("LEDGER_BACKEND", "memory"),
            dsn=os.getenv("LEDGER_DSN", ""),
            pool_size=int(os.getenv("LEDGER_POOL_SIZE", "5")),
            timeout=int(os.getenv("LEDGER_TIMEOUT", "30")),
        )
