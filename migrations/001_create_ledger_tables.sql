-- Migration 001: Create Autonomous Verification Ledger tables
-- Phase 13: Hash-linked, append-only ledger for cross-slot trust provenance
-- Date: 2025-10-27

-- Ledger records table (append-only)
CREATE TABLE IF NOT EXISTS ledger_records (
    rid TEXT PRIMARY KEY,
    anchor_id TEXT NOT NULL,
    slot TEXT NOT NULL,
    kind TEXT NOT NULL,
    ts TIMESTAMP NOT NULL,
    prev_hash TEXT,
    hash TEXT NOT NULL UNIQUE,
    payload JSONB NOT NULL,
    sig BYTEA,
    producer TEXT NOT NULL,
    version TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_ledger_anchor_ts ON ledger_records(anchor_id, ts);
CREATE INDEX IF NOT EXISTS idx_ledger_slot_kind_ts ON ledger_records(slot, kind, ts);
CREATE INDEX IF NOT EXISTS idx_ledger_hash ON ledger_records(hash);
CREATE INDEX IF NOT EXISTS idx_ledger_ts ON ledger_records(ts);

-- Checkpoints table (periodic Merkle roots)
CREATE TABLE IF NOT EXISTS ledger_checkpoints (
    cid TEXT PRIMARY KEY,
    range_start TEXT NOT NULL,
    range_end TEXT NOT NULL,
    merkle_root TEXT NOT NULL,
    sig BYTEA,
    record_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_checkpoint_created ON ledger_checkpoints(created_at DESC);

-- Comments for documentation
COMMENT ON TABLE ledger_records IS 'Append-only ledger of cross-slot verification events';
COMMENT ON COLUMN ledger_records.rid IS 'UUIDv7 for time-ordered identifiers';
COMMENT ON COLUMN ledger_records.prev_hash IS 'SHA3-256 of previous record for this anchor_id';
COMMENT ON COLUMN ledger_records.hash IS 'SHA3-256 of this record''s canonical representation';
COMMENT ON COLUMN ledger_records.payload IS 'Event-specific data as canonical JSON';
COMMENT ON COLUMN ledger_records.sig IS 'Optional PQC signature (Dilithium2)';

COMMENT ON TABLE ledger_checkpoints IS 'Periodic Merkle root checkpoints for batch verification';
COMMENT ON COLUMN ledger_checkpoints.merkle_root IS 'SHA3-256 Merkle root of record hashes in range';
COMMENT ON COLUMN ledger_checkpoints.sig IS 'PQC signature over checkpoint (Dilithium2)';
