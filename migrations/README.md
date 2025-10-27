# Nova Ledger Migrations

Database migrations for the Autonomous Verification Ledger (Phase 13).

## Applying Migrations

### PostgreSQL
```bash
psql -d nova -f migrations/001_create_ledger_tables.sql
```

### SQLite (Development)
```bash
sqlite3 nova.db < migrations/001_create_ledger_tables.sql
```

## Migration History

- **001_create_ledger_tables.sql** (2025-10-27, Phase 13)
  - Creates `ledger_records` table (append-only record chain)
  - Creates `ledger_checkpoints` table (Merkle root snapshots)
  - Adds indexes for efficient queries by anchor_id, slot, kind, timestamp
