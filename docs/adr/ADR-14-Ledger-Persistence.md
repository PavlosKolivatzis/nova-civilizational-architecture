# ADR-14: Ledger Persistence

## Status
Accepted

## Context
The Autonomous Verification Ledger (AVL) currently uses an in-memory store for hash-linked records. While this provides fast access and ensures continuity during runtime, it lacks durability and horizontal scalability. Phase 13 introduced the ledger for cross-slot trust provenance, but production deployments need persistent storage to survive restarts and enable multi-instance deployments.

## Decision
Implement PostgreSQL persistence for the AVL using SQLAlchemy 2.x async drivers, with automatic fallback to in-memory storage on database unavailability.

### Schema Design
```sql
CREATE TABLE ledger_records (
    rid UUID PRIMARY KEY,
    anchor_id UUID NOT NULL,
    slot TEXT NOT NULL,
    kind TEXT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    prev_hash CHAR(64),
    hash CHAR(64) UNIQUE NOT NULL,
    payload JSONB NOT NULL,
    sig BYTEA,
    producer TEXT,
    version TEXT DEFAULT 'v1'
);

CREATE TABLE ledger_checkpoints (
    cid UUID PRIMARY KEY,
    range_start TEXT NOT NULL,
    range_end TEXT NOT NULL,
    merkle_root CHAR(64),
    sig BYTEA,
    created_at TIMESTAMPTZ DEFAULT now(),
    record_count INTEGER DEFAULT 0
);

CREATE INDEX idx_records_anchor_ts ON ledger_records(anchor_id, ts);
```

### Configuration
```yaml
ledger:
  backend: postgres  # or 'memory'
  dsn: postgresql+asyncpg://nova:pass@localhost:5432/nova
  pool_size: 5
  timeout: 30
```

Environment variables:
- `LEDGER_BACKEND={memory|postgres}`
- `LEDGER_DSN=postgresql+asyncpg://...`
- `LEDGER_POOL_SIZE=5`
- `LEDGER_TIMEOUT=30`

### Implementation
- `PostgresLedgerStore`: Async SQLAlchemy implementation maintaining full `LedgerStore` interface compatibility
- `create_ledger_store()`: Factory function with automatic fallback logic
- Alembic migrations for schema management
- Comprehensive test coverage including concurrent operations

## Consequences

### Positive
- **Durability**: Records persist across restarts
- **Scalability**: Multiple instances can share ledger state
- **Observability**: Rich metrics for persistence operations
- **Reliability**: Graceful fallback maintains service availability
- **Performance**: Connection pooling and async operations

### Negative
- **Dependency**: PostgreSQL becomes a critical dependency
- **Complexity**: Additional configuration and operational overhead
- **Migration**: One-time data migration from existing in-memory state

### Risks
- **Data Loss**: Migration window requires careful planning
- **Performance**: Network latency vs. in-memory speed trade-off
- **Locking**: Concurrent writes need careful handling

## Alternatives Considered

### Alternative 1: Embedded Database (SQLite)
- **Pros**: No external dependencies, file-based persistence
- **Cons**: Limited concurrency, not suitable for multi-instance deployments

### Alternative 2: Document Store (MongoDB)
- **Pros**: Natural fit for JSON payloads, flexible schema
- **Cons**: Additional complexity, operational overhead

### Alternative 3: Keep In-Memory Only
- **Pros**: Simplicity, performance
- **Cons**: No persistence, single-instance limitation

## Implementation Plan

### Phase 1: Core Implementation
- [x] PostgreSQL store implementation
- [x] Schema migrations
- [x] Configuration system
- [x] Factory with fallback logic
- [x] Basic metrics

### Phase 2: Testing & Validation
- [x] Unit tests for PostgreSQL operations
- [x] Integration tests with real database
- [x] Concurrent write testing
- [x] Migration verification

### Phase 3: Observability
- [x] Prometheus metrics for persistence
- [x] Grafana dashboards
- [x] Alerting rules

### Phase 4: Operations
- [x] CLI migration tool
- [x] Health checks
- [x] Rollback procedures

## Rollback Plan
1. Set `LEDGER_BACKEND=memory` in configuration
2. Restart service (new records go to memory store)
3. Monitor for any persistence-related errors
4. If needed, scale down to single instance during rollback window

## Success Metrics
- **Availability**: 99.9% ledger backend uptime
- **Performance**: P95 write latency < 25ms
- **Correctness**: Zero continuity breaks post-migration
- **Observability**: < 1% gap in persistence metrics

## Future Considerations
- **Sharding**: Horizontal scaling beyond single PostgreSQL instance
- **Archiving**: Long-term record archival strategies
- **Encryption**: At-rest encryption for sensitive ledger data
- **Backup**: Automated backup and recovery procedures