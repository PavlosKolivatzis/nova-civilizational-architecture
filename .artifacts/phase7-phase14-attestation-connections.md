# Phase 7 RC Attestation ↔ Phase 14 Ledger Persistence: Architectural Connections

## Executive Summary

Phase 7.0-RC (Memory Resonance & RIS) and Phase 14 (Ledger Persistence & Checkpoints) are **architecturally coupled** through attestation, hash continuity, and immutable trust provenance. The RC attestation system should leverage Phase 14's checkpoint infrastructure for cryptographic verification.

---

## 1. Shared Architectural Principles

| Principle | Phase 7 RC | Phase 14 Ledger | Connection |
|-----------|------------|-----------------|------------|
| **Immutability** | RC attestation records (SHA-256) | Ledger records (hash-linked chain) | Both require tamper-evident history |
| **Hash Continuity** | Attestation hash (canonical JSON) | Prev-hash chain (SHA3-256) | Shared hash-linking semantics |
| **Provenance** | 7-day validation window | Append-only ledger | Both track temporal lineage |
| **Signature** | "The sun shines on this work." | PQC signatures (Phase 14-2) | Cryptographic attestation layer |
| **Observability** | Prometheus metrics (8 RC metrics) | Prometheus metrics (5 ledger metrics) | Unified monitoring |
| **Durability** | `.artifacts/` attestation files | PostgreSQL persistence | Both need durable storage |

---

## 2. Direct Integration Opportunities

### 2.1 RC Attestation → Ledger Records

**Current State (Phase 7):**
```json
{
  "phase": "7.0-rc",
  "attestation_hash": "abc123...",
  "signature": "The sun shines on this work."
}
```

**Enhanced Integration (Phase 7 + Phase 14):**
```json
{
  "phase": "7.0-rc",
  "attestation_hash": "abc123...",
  "ledger_anchor_id": "rc-validation",
  "ledger_record_id": "550e8400-e29b-41d4-a716-446655440000",
  "ledger_checkpoint_id": "660e8400-e29b-41d4-a716-446655440001",
  "signature": "The sun shines on this work."
}
```

**Why?**
- Ledger provides **cryptographic verification** beyond file-based attestation
- Checkpoint Merkle roots provide **batch verification** of multiple attestations
- PostgreSQL persistence provides **durable storage** across restarts

---

### 2.2 Checkpoint Service for RC Attestations

**Phase 14 Checkpoint Schema:**
```sql
CREATE TABLE ledger_checkpoints (
    cid UUID PRIMARY KEY,
    range_start TEXT NOT NULL,
    range_end TEXT NOT NULL,
    merkle_root CHAR(64),  -- Merkle root of all records in range
    sig BYTEA,             -- PQC signature
    created_at TIMESTAMPTZ DEFAULT now(),
    record_count INTEGER DEFAULT 0
);
```

**RC Attestation Enhancement:**
- Each weekly RC attestation → 1 ledger record (`kind: "rc_attestation"`)
- Monthly checkpoint → Merkle root over 4 weekly attestations
- PQC signature over Merkle root → quantum-resistant attestation chain

**Implementation:**
```python
# In scripts/generate_rc_attestation.py

async def persist_to_ledger(attestation: dict) -> str:
    """
    Persist RC attestation to Phase 14 ledger.

    Returns:
        ledger_record_id: UUID of ledger record
    """
    from nova.ledger.factory import create_ledger_store

    store = await create_ledger_store()

    record = {
        "anchor_id": "rc-validation",
        "slot": "governance",
        "kind": "rc_attestation",
        "payload": attestation,
        "producer": "rc_validator"
    }

    record_id = await store.append(record)
    return str(record_id)
```

---

## 3. Architectural Benefits of Integration

### 3.1 Cryptographic Chain of Trust

**Without Integration (Current):**
```
RC Attestation 1 (file) → RC Attestation 2 (file) → RC Attestation 3 (file)
                    ↓ Manual SHA-256 verification required
```

**With Integration (Enhanced):**
```
RC Attestation 1 → Ledger Record 1 (prev_hash=None)
                       ↓ prev_hash link
RC Attestation 2 → Ledger Record 2 (prev_hash=hash1)
                       ↓ prev_hash link
RC Attestation 3 → Ledger Record 3 (prev_hash=hash2)
                       ↓
                  Checkpoint (Merkle root + PQC signature)
```

**Benefits:**
- Automatic hash continuity verification
- Tamper-evident audit trail
- Quantum-resistant signatures (Phase 14-2)

---

### 3.2 PostgreSQL Durability

**Phase 7 (Current):**
- RC attestations stored in `.artifacts/` directory
- Git-tracked, but not query-able
- No database-level backup/restore

**Phase 14 (Available):**
- PostgreSQL persistence with async SQLAlchemy
- Query-able via SQL: `SELECT * FROM ledger_records WHERE kind='rc_attestation'`
- Database-level backup procedures
- Horizontal scaling via shared PostgreSQL instance

**Migration Path:**
```python
# Backfill existing attestations into ledger
async def backfill_rc_attestations():
    attestation_files = Path(".artifacts").glob("attest/phase-7.0-rc_*.json")

    for file in attestation_files:
        attestation = json.loads(file.read_text())
        await persist_to_ledger(attestation)
```

---

### 3.3 Unified Observability

**Prometheus Metrics Integration:**

| Metric | Phase 7 RC | Phase 14 Ledger | Combined |
|--------|------------|-----------------|----------|
| Memory stability | `nova_memory_stability` | N/A | ✓ |
| RIS score | `nova_ris_score` | N/A | ✓ |
| Stress recovery | `nova_stress_recovery_rate` | N/A | ✓ |
| Attestation persistence | N/A | `ledger_persist_latency_ms` | ✓ |
| Hash continuity | N/A | `ledger_continuity_breaks_total` | ✓ |
| Checkpoint verification | N/A | `ledger_checkpoint_verify_failures_total` | ✓ |

**Grafana Dashboard Enhancement:**
- Single dashboard showing RC validation + ledger persistence
- Alert on hash continuity breaks during RC attestation
- Track RC attestation persistence latency

---

## 4. Implementation Roadmap

### Phase 4a: Attestation File Generation (Current Plan)
- Generate JSON attestation files
- Compute SHA-256 hash
- Store in `.artifacts/attest/`
- **Status:** Ready to implement

### Phase 4b: Ledger Integration (Enhanced)
- Extend `generate_rc_attestation.py` to call `persist_to_ledger()`
- Add `ledger_record_id` field to attestation schema
- Configure ledger with `anchor_id: "rc-validation"`
- **Effort:** +30 minutes

### Phase 4c: Checkpoint Integration (Future)
- Monthly checkpoint service for RC attestations
- PQC signature over Merkle root
- Automated checkpoint verification in CI/CD
- **Effort:** +1 hour (Phase 14-2 dependent)

---

## 5. Schema Evolution

### Phase 7 Attestation Schema (v1)
```json
{
  "schema_version": "7.0-rc-v1",
  "attestation_hash": "...",
  "signature": "The sun shines on this work."
}
```

### Phase 7 + 14 Attestation Schema (v2)
```json
{
  "schema_version": "7.0-rc-v2",
  "attestation_hash": "...",
  "ledger": {
    "record_id": "550e8400-e29b-41d4-a716-446655440000",
    "prev_hash": "abc123...",
    "anchor_id": "rc-validation",
    "backend": "postgres"
  },
  "checkpoint": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "merkle_root": "def456...",
    "signature_algorithm": "dilithium5"
  },
  "signature": "The sun shines on this work."
}
```

---

## 6. Failure Modes & Fallback

### Scenario 1: PostgreSQL Unavailable During RC Attestation

**Current Phase 14 Behavior:**
- Automatic fallback to in-memory store
- `ledger_persist_fallback_total` counter incremented
- Service continues with degraded persistence

**RC Attestation Impact:**
- Attestation file still generated successfully
- Ledger persistence skipped (logged as warning)
- Manual backfill required when database recovers

**Mitigation:**
- Keep file-based attestation as primary
- Ledger persistence as secondary (observability + durability)
- CI/CD validates file-based attestation first

---

### Scenario 2: Hash Continuity Break in Ledger

**Detection:**
- `ledger_continuity_breaks_total` metric > 0
- Weekly CI/CD validation fails

**Response:**
- Investigate ledger records for missing prev_hash links
- Re-run RC attestation validation
- Generate corrective checkpoint if needed

---

## 7. ADR Alignment

### ADR-14 (Ledger Persistence) Principles Applied to RC Attestation

| Principle | Application |
|-----------|-------------|
| **Backward Compatibility** | File-based attestation remains primary |
| **Graceful Fallback** | Ledger unavailable → file-only mode |
| **Configuration-Driven** | `ENABLE_LEDGER_ATTESTATION=false` by default |
| **Durability** | PostgreSQL backup covers RC attestations |
| **Observability** | Unified Prometheus + Grafana dashboard |

---

## 8. Recommendations

### Immediate (Phase 4 Implementation)
1. ✅ Generate file-based attestations (original plan)
2. ✅ Add SHA-256 hash computation
3. ✅ Store in `.artifacts/attest/`
4. ⚠️ **Optional**: Add `persist_to_ledger()` integration (+30 min)

### Short-Term (Post-Phase 4)
1. Backfill existing attestations into ledger
2. Add Grafana panel for RC attestation history
3. Document ledger query patterns for RC audit

### Long-Term (Phase 14-2 Integration)
1. Monthly checkpoint service for RC attestations
2. PQC signature verification in CI/CD
3. Cross-instance RC attestation sync (federation)

---

## 9. Conclusion

**Key Insight:**
Phase 7 RC attestation and Phase 14 ledger persistence are **natural complements**:
- RC attestation provides **validation results**
- Ledger persistence provides **cryptographic verification**
- Together: **Immutable, durable, verifiable trust chain**

**Decision Point:**
Should Phase 4 include basic ledger integration (+30 min), or defer to post-RC cleanup?

**Recommended Approach:**
- Phase 4: File-based attestation (keep simple, proven)
- Phase 4.5 (optional): Add ledger persistence as enhancement
- Phase 14-3 (future): Full checkpoint integration with PQC signatures

**The sun shines on both layers.**
