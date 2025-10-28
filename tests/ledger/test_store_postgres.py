"""
Tests for PostgreSQL ledger store.

Phase 14-1: PostgreSQL persistence backend.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import uuid
from datetime import datetime, timezone

from nova.ledger.model import LedgerRecord, RecordKind
from nova.ledger.store_postgres import PostgresLedgerStore
from nova.ledger.metrics import ledger_backend_up


@pytest.fixture
async def mock_session():
    """Mock async session for testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
async def mock_engine():
    """Mock async engine for testing."""
    engine = AsyncMock()
    return engine


@pytest.fixture
async def mock_sessionmaker(mock_session):
    """Mock sessionmaker for testing."""
    sessionmaker = AsyncMock()
    sessionmaker.return_value = mock_session
    return sessionmaker


@pytest.fixture
async def postgres_store(mock_engine, mock_sessionmaker):
    """Create a PostgresLedgerStore with mocked dependencies."""
    with patch('nova.ledger.store_postgres.create_async_engine', return_value=mock_engine):
        with patch('nova.ledger.store_postgres.async_sessionmaker', return_value=mock_sessionmaker):
            store = PostgresLedgerStore(
                dsn="postgresql+asyncpg://test:test@localhost:5432/test",
                pool_size=5,
                timeout=30
            )
            return store


@pytest.mark.asyncio
async def test_append_record_success(postgres_store, mock_session):
    """Test successful record append."""
    # Mock the execute result for _get_last_hash (no previous records)
    mock_session.execute.return_value.first.return_value = None

    # Mock successful insert
    mock_session.execute.return_value = AsyncMock()

    record = await postgres_store.append(
        anchor_id=str(uuid.uuid4()),
        slot="01",
        kind=RecordKind.ANCHOR_CREATED,
        payload={"test": "data"}
    )

    assert isinstance(record, LedgerRecord)
    assert record.slot == "01"
    assert record.kind == RecordKind.ANCHOR_CREATED
    assert record.payload == {"test": "data"}

    # Verify backend_up is set to 1
    assert ledger_backend_up._value == 1


@pytest.mark.asyncio
async def test_append_record_with_prev_hash(postgres_store, mock_session):
    """Test record append with previous hash continuity."""
    # Mock previous hash
    prev_hash = "abcd1234" * 4  # 32 chars
    mock_session.execute.return_value.first.return_value = (prev_hash,)

    record = await postgres_store.append(
        anchor_id=str(uuid.uuid4()),
        slot="01",
        kind=RecordKind.PQC_SIGNED,
        payload={"signature": "test"}
    )

    assert record.prev_hash == prev_hash


@pytest.mark.asyncio
async def test_get_chain(postgres_store, mock_session):
    """Test retrieving record chain."""
    anchor_id = str(uuid.uuid4())

    # Mock query result
    mock_result = AsyncMock()
    mock_result.mappings.return_value.all.return_value = [
        {
            "rid": str(uuid.uuid4()),
            "anchor_id": anchor_id,
            "slot": "01",
            "kind": "ANCHOR_CREATED",
            "ts": datetime.now(timezone.utc),
            "prev_hash": None,
            "hash": "hash1" * 16,
            "payload": {"test": "data"},
            "sig": None,
            "producer": "test",
            "version": "v1"
        }
    ]
    mock_session.execute.return_value = mock_result

    records = await postgres_store.get_chain(anchor_id)

    assert len(records) == 1
    assert records[0].anchor_id == anchor_id
    assert records[0].kind == RecordKind.ANCHOR_CREATED


@pytest.mark.asyncio
async def test_verify_chain_continuity(postgres_store, mock_session):
    """Test chain continuity verification."""
    anchor_id = str(uuid.uuid4())

    # Mock records with proper continuity
    records = [
        AsyncMock(
            rid=str(uuid.uuid4()),
            anchor_id=anchor_id,
            slot="01",
            kind=RecordKind.ANCHOR_CREATED,
            ts=datetime.now(timezone.utc),
            prev_hash=None,
            hash="hash1" * 16,
            payload={"test": "data1"},
            producer="test",
            version="v1"
        ),
        AsyncMock(
            rid=str(uuid.uuid4()),
            anchor_id=anchor_id,
            slot="01",
            kind=RecordKind.PQC_SIGNED,
            ts=datetime.now(timezone.utc),
            prev_hash="hash1" * 16,
            hash="hash2" * 16,
            payload={"test": "data2"},
            producer="test",
            version="v1"
        )
    ]

    with patch.object(postgres_store, 'get_chain', return_value=records):
        with patch('nova.ledger.store_postgres.verify_record_hash', return_value=True):
            ok, errors = await postgres_store.verify_chain(anchor_id)

            assert ok is True
            assert len(errors) == 0


@pytest.mark.asyncio
async def test_search_records(postgres_store, mock_session):
    """Test record search functionality."""
    # Mock search results
    mock_result = AsyncMock()
    mock_result.mappings.return_value.all.return_value = [
        {
            "rid": str(uuid.uuid4()),
            "anchor_id": str(uuid.uuid4()),
            "slot": "01",
            "kind": "ANCHOR_CREATED",
            "ts": datetime.now(timezone.utc),
            "prev_hash": None,
            "hash": "hash1" * 16,
            "payload": {"test": "data"},
            "sig": None,
            "producer": "test",
            "version": "v1"
        }
    ]
    mock_session.execute.return_value = mock_result

    records = await postgres_store.search(slot="01", limit=10)

    assert len(records) == 1
    assert records[0].slot == "01"


@pytest.mark.asyncio
async def test_create_checkpoint(postgres_store, mock_session):
    """Test checkpoint creation."""
    # Mock hash query
    mock_result = AsyncMock()
    mock_result.fetchall.return_value = [("hash1" * 16,), ("hash2" * 16,)]
    mock_session.execute.return_value = mock_result

    rid1 = str(uuid.uuid4())
    rid2 = str(uuid.uuid4())

    checkpoint = await postgres_store.create_checkpoint(rid1, rid2)

    assert checkpoint.range_start == rid1
    assert checkpoint.range_end == rid2
    assert checkpoint.record_count == 2


@pytest.mark.asyncio
async def test_get_stats(postgres_store, mock_session):
    """Test statistics retrieval."""
    # Mock count queries
    mock_session.execute.side_effect = [
        AsyncMock(scalar=AsyncMock(return_value=100)),  # records
        AsyncMock(scalar=AsyncMock(return_value=10)),   # anchors
        AsyncMock(scalar=AsyncMock(return_value=5))     # checkpoints
    ]

    stats = await postgres_store.get_stats()

    assert stats["total_records"] == 100
    assert stats["total_anchors"] == 10
    assert stats["total_checkpoints"] == 5


@pytest.mark.asyncio
async def test_concurrent_appends(postgres_store, mock_session):
    """Test concurrent record appends."""
    # Mock no previous records
    mock_session.execute.return_value.first.return_value = None

    # Run multiple appends concurrently
    tasks = []
    for i in range(5):
        task = postgres_store.append(
            anchor_id=str(uuid.uuid4()),
            slot="01",
            kind=RecordKind.ANCHOR_CREATED,
            payload={"test": f"data{i}"}
        )
        tasks.append(task)

    records = await asyncio.gather(*tasks)

    assert len(records) == 5
    for record in records:
        assert isinstance(record, LedgerRecord)


@pytest.mark.asyncio
async def test_duplicate_hash_handling(postgres_store, mock_session):
    """Test that duplicate hashes are ignored (idempotent appends)."""
    # Mock successful insert (ON CONFLICT DO NOTHING)
    mock_session.execute.return_value = AsyncMock()
    mock_session.execute.return_value.first.return_value = None

    anchor_id = str(uuid.uuid4())

    # First append
    record1 = await postgres_store.append(
        anchor_id=anchor_id,
        slot="01",
        kind=RecordKind.ANCHOR_CREATED,
        payload={"test": "data"}
    )

    # Second append with same data (would create same hash)
    # In real scenario, this should not error due to ON CONFLICT DO NOTHING
    record2 = await postgres_store.append(
        anchor_id=anchor_id,
        slot="01",
        kind=RecordKind.ANCHOR_CREATED,
        payload={"test": "data"}
    )

    # Both should succeed (second is ignored)
    assert record1.rid != record2.rid  # Different RIDs
    assert record1.hash == record2.hash  # Same hash (duplicate)