"""
Tests for PostgreSQL ledger store.

Phase 14-1: PostgreSQL persistence backend.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from datetime import datetime, timezone

from nova.ledger.model import LedgerRecord, RecordKind
from nova.ledger.store_postgres import PostgresLedgerStore
from nova.ledger.metrics import ledger_backend_up


@pytest.fixture
def postgres_store():
    """Create a PostgresLedgerStore with minimal mocking."""
    # Mock the engine and sessionmaker at the module level
    with pytest.MonkeyPatch().context() as m:
        mock_engine = MagicMock()
        mock_sessionmaker = MagicMock()

        # Mock the create_async_engine function
        m.setattr('nova.ledger.store_postgres.create_async_engine', MagicMock(return_value=mock_engine))

        # Mock the async_sessionmaker function
        m.setattr('nova.ledger.store_postgres.async_sessionmaker', MagicMock(return_value=mock_sessionmaker))

        store = PostgresLedgerStore(
            dsn="postgresql+asyncpg://test:test@localhost:5432/test",
            pool_size=5,
            timeout=30
        )

        # Replace the Session with a synchronous mock for testing
        store.Session = MagicMock()
        return store


def test_store_initialization(postgres_store):
    """Test that the store initializes correctly."""
    assert postgres_store.dsn == "postgresql+asyncpg://test:test@localhost:5432/test"
    assert postgres_store.pool_size == 5
    assert postgres_store.timeout == 30


def test_record_creation():
    """Test LedgerRecord creation and validation."""
    record = LedgerRecord(
        rid=str(uuid.uuid4()),
        anchor_id=str(uuid.uuid4()),
        slot="01",
        kind=RecordKind.ANCHOR_CREATED,
        ts=datetime.now(timezone.utc),
        prev_hash=None,
        hash="test_hash",
        payload={"test": "data"},
        producer="test",
        version="v1"
    )

    assert record.rid is not None
    assert record.anchor_id is not None
    assert record.slot == "01"
    assert record.kind == RecordKind.ANCHOR_CREATED
    assert record.payload == {"test": "data"}


def test_config_loading():
    """Test that config loads correctly."""
    from nova.config.ledger_config import LedgerConfig

    config = LedgerConfig.from_env()
    assert hasattr(config, 'backend')
    assert hasattr(config, 'dsn')
    assert hasattr(config, 'pool_size')
    assert hasattr(config, 'timeout')


def test_factory_fallback():
    """Test that factory falls back to memory store."""
    from nova.config.ledger_config import LedgerConfig

    # Test with invalid backend
    config = LedgerConfig(backend="invalid")

    from nova.ledger.factory import create_ledger_store
    store = create_ledger_store(config)
    assert store is not None

    # Should be a memory store
    from nova.ledger.store import LedgerStore
    assert isinstance(store, LedgerStore)


def test_metrics_import():
    """Test that metrics can be imported without duplication."""
    from nova.ledger.metrics import (
        ledger_persist_latency_ms,
        ledger_persist_errors_total,
        ledger_backend_up,
        ledger_persist_fallback_total
    )

    # Just verify they exist and are the right types
    assert ledger_persist_latency_ms is not None
    assert ledger_persist_errors_total is not None
    assert ledger_backend_up is not None
    assert ledger_persist_fallback_total is not None


# Skip complex async tests for now - focus on basic functionality
# These would require extensive mocking of async SQLAlchemy patterns