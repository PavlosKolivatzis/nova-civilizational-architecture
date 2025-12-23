# Changelog

All notable changes to Nova Civilizational Architecture will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- **Phase 15-8.2: Adaptive Wisdom Governor Integration** (v15.8.2) — Wisdom governor wired into operational nervous system: Slot 4 (TRI) contributes coherence-based learning caps; Slot 7 (Production Controls) adjusts concurrency via stability-driven backpressure; GovernorState provides single source of truth for η across all training loops. Nova becomes self-tuning: sensing stability margins in real time, scaling learning and exertion autonomously.
- **ADR-Reflection-15: Federation as the Birth of Shared Truth** — Canonical reflection on Phase 15's epistemic and architectural meaning
  - Philosophical foundation for federated checkpoint synchronization
  - Evolution from isolated attestation to dialogic coherence
  - Decentralization of epistemic authority while maintaining node sovereignty
  - Trust as measurable gradient rather than binary flag
  - Civilizational parameters for digital trust systems
  - Key insight: "Integrity that never meets another remains sterile; only through federation does truth become civilization."

### Governance
- **Tag `governance-topology-seal`** – Authorization topology sealed: "autonomous" scope clarified as internal evaluation only, perimeter enforcement made explicit for operator endpoints, default-inversion invariant documented, and observability-only metrics locked unless explicitly authorized.

## [15.2.0-alpha] - 2025-11-02
### Added
- **Phase 15-3: Federation Range Sync & Discovery**
  - Range proof API (`GET /federation/checkpoints/latest`, `POST /federation/range_proof`) with bounded chunks (`NOVA_FEDERATION_RANGE_MAX`, `NOVA_FEDERATION_CHUNK_BYTES_MAX`) and hashed continuity digests.
  - Client `RangeSyncer` orchestrating range fetch/verify, divergence enforcement (`NOVA_FEDERATION_MAX_DIVERGENCE`), continuity/divergence receipts, and OpenTelemetry spans.
  - Signed peer manifest discovery (`ManifestCache`, `ManifestVerifier`) with rotation receipts and `federation_manifest_rotations_total` metric (`NOVA_FEDERATION_MANIFEST_TTL_S`).
  - New Prometheus metrics: `federation_range_bytes_total`, `federation_range_chunks_total{result}`, `federation_divergences_total`, `federation_manifest_rotations_total`.
  - Grafana dashboard refresh (`monitoring/grafana/federation-health.json`) with range/divergence/manifests panels.
  - Tests covering range proofs, sync flow, divergence policy, manifest rotation, metrics, and tracing (`tests/federation/test_*.py` additions).

## [15.1.0-alpha] - 2025-10-31
### Added
- **Phase 15-2: Gradient Trust & Manifest Preparation**
  - Gradient trust scoring exposed alongside boolean verification.
  - OpenAPI documentation for federation endpoints with `{code, reason}` errors.
  - httpx-based federation client retries + metrics.

## [14.0.0-alpha] - 2025-10-31
### Added
- **Phase 14-2: Merkle Checkpoints + PQC Signer** — Complete autonomous verification ledger with quantum-resistant signing
- Merkle tree builder with SHA3-256 hashing, proof generation, and verification
- PQC checkpoint signing using Dilithium2 via shared keyring infrastructure
- CheckpointSigner with canonical byte representation and signature verification
- CheckpointService with configurable intervals (`every_seconds`, `min_records`) and enable/disable flag
- REST API endpoints: `POST /ledger/checkpoints/`, `GET /ledger/checkpoints/{anchor_id}`, `POST /ledger/checkpoints/verify`
- Checkpoint persistence in PostgreSQL (`ledger_checkpoints` table)
- Metrics: `ledger_checkpoints_total`, `ledger_checkpoint_verify_failures_total`
- 73 ledger tests covering Merkle operations, signing, verification, and API endpoints
- Python 3.10-3.13 compatibility with `from __future__ import annotations`

### Performance
- **Health system caching optimization** — Eliminated 60% performance degradation under sustained load
- Module-level caching for slot health imports
- Instance-level caching for slot processors (TruthAnchorEngine, DeltaThreshProcessor)
- Sustained load test now passes: performance degradation <1.5x (was 1.6x)
- Eliminated 1000+ redundant initialization log messages

### Fixed
- Prometheus metrics: Prevented duplicate ProcessCollector registration in CI
- Test isolation: Added `clear_slot_health_cache()` for clean test state
- API dependency injection: Override pattern for proper mock injection in tests
- Python 3.10 compatibility: Future annotations for union type syntax in dataclasses

### Documentation
- ADR-Reflection-15: Federation as the Birth of Shared Truth
- Updated ledger test documentation with new API signatures

## [13.1.0] — 2025-10-29
### Added
- **PostgreSQL Persistence for AVL** — Phase 14-1 complete: durable, async ledger storage
- Async SQLAlchemy 2.x writer/reader with connection pooling and timeout management
- Automatic fallback to in-memory store on database unavailability (`ledger_persist_fallback_total`)
- Alembic migration `202510281200_add_ledger_pg.py`: `ledger_records`, `ledger_checkpoints` tables
- CLI migration tool: `scripts/ledger_migrate.py` (check-db, upgrade, current, history)
- Enhanced Prometheus metrics: `ledger_persist_latency_ms`, `ledger_persist_errors_total`, `ledger_backend_up`
- Grafana dashboard: `nova-phase14-ledger-persistence.json` with latency, errors, and health panels
- Configuration: `LEDGER_BACKEND={memory|postgres}`, `LEDGER_DSN`, `LEDGER_POOL_SIZE`, `LEDGER_TIMEOUT`
- Factory pattern: `create_ledger_store()` with graceful degradation
- 5 PostgreSQL integration tests: round-trip, continuity, idempotency, concurrency
- ADR-14-Ledger-Persistence.md: design decisions, rollback plan, success metrics

### Changed
- Ledger store: now supports both memory and PostgreSQL backends via configuration
- Metrics: unified Phase 13/14 observability with persistence-specific counters

### Security/Integrity
- Hash continuity preserved across storage backends (Merkle root parity verified)
- Connection pooling prevents resource exhaustion under load
- Fallback mechanism maintains service availability during database outages

### Next
- Phase 14-2: Automated Merkle checkpoint signing with PQC verification
- Phase 14-3: IDS/routing integration with trust scores from persisted ledger

## [13.0.0-beta] — 2025-10-27
### Added
- **Autonomous Verification Ledger (AVL)** — Hash-linked, append-only ledger for cross-slot trust propagation
- SHA3-256 hash chains with prev_hash continuity for tamper detection
- Composite trust scoring: `T = 0.5·F̄ + 0.2·pqc_rate + 0.2·verify_rate + 0.1·continuity`
- Canonical JSON serialization for deterministic hashing
- Merkle checkpoint support for batch verification
- Slot emitters: Slot01 (`ANCHOR_CREATED`), Slot02 (`DELTATHRESH_APPLIED`), Slot08 (`PQC_VERIFIED`, `PQC_KEY_ROTATED`)
- REST API: `/ledger/append`, `/ledger/chain/{id}`, `/ledger/verify/{id}`, `/ledger/stats`
- Prometheus metrics: `ledger_appends_total`, `ledger_trust_score`, `ledger_chain_length`
- LedgerClient singleton with shared store for cross-component visibility
- PostgreSQL migration schema ready (`migrations/001_create_ledger_tables.sql`)
- 60 ledger + integration tests (canon, store, verify, end-to-end)
- Configuration: 5 `LEDGER_*` environment variables with defaults
- ADR-13-Ledger-Final.md documenting architecture decisions

### Security/Integrity
- PQC-verifiable signatures (Dilithium2) in ledger records
- Cryptographic tamper detection via hash chain verification
- Fidelity metrics from quantum entropy integrated into trust scores
- All critical events (anchor creation, PQC verification, fidelity weighting) now ledger-tracked

### Next
- Phase 14-1: PostgreSQL persistence with async writer ✅ **COMPLETED**
- Phase 14-2: Automated Merkle checkpoint signing
- Phase 14-3: IDS/routing integration with trust scores

## [11.1-pre] — 2025-10-25
### Added
- ARC calibration experiment: full infra (CI, alerts, Grafana, schema)
- Reflection engine metrics: `nova_arc_precision`, `nova_arc_recall`, `nova_arc_drift`
- Reproducibility: `make reproduce-arc-experiment`, weekly CI run, artifacts
- Adversarial domain generation: spectral match, equilibrium mismatch, shield bypass
- Ablation studies: validate necessity of spectral, equilibrium, and shield components
- Scientific falsification protocol: pre-registered conditions for hypothesis invalidation
- arXiv paper draft: "Universal Structure Mathematics and Autonomous Reflection in Nova"
- CITATION.cff: academic citation metadata for reproducible research
- Slot01 Quantum Entropy: simulator adapter, entropy metadata, Prometheus metrics, Alembic migration, and tests

### Security/Integrity
- Vault attest on every second cycle; final snapshot archived
- JSON schema validation for all experiment results
- Cryptographic audit trails throughout calibration process

### Next
- Promote to v11.1-beta upon meeting precision/recall/drift gates over 48h stability
- Submit arXiv preprint and Zenodo reproducibility package

## [11.0-final] — 2025-10-24
### Added
- Universal Structure Mathematics: spectral graph theory + equilibrium analysis
- Phase 11 complete: mathematical proof of structural identity across domains
- Dynamic simulations: extraction-harm-regulation feedback models
- Complete audit trail: from vault corruption investigation to final resolution
- Phase 11B foundation: ARC reflection engine scaffolding and sprint plan

### Changed
- Repository structure: all Phase 11 features integrated into main branch
- Documentation: comprehensive mathematical foundations and experimental protocols

### Fixed
- Vault corruption: complete recovery with zero data loss
- Commit integrity: full investigation and resolution of Phase 11 errors

## [10.0-final] — 2025-10-21
### Added
- Ethical Autonomy & Federated Cognition: Phase 10 complete
- FEP, PCR, AG, CIG, FLE-II modules operational
- TRI score 0.81, resilience class B, maturity level 4.0

### Changed
- Architecture: federated ethical reasoning at planetary scale
- Governance: autonomous ethical decision-making

## [9.0-final] — 2025-10-20
### Added
- Adaptive Civilizational Networks: Phase 9 complete
- Network fusion and continuity preservation
- Vault integrity: cryptographic continuity chain established

## [8.0-gold] — 2025-10-20
### Added
- Continuity Engine: Phase 8 complete
- Temporal coherence and state preservation
- Gold standard certification achieved

## [7.0-rc-complete] — 2025-10-20
### Added
- Temporal Resonance: Phase 7 complete
- TRSI and TRSI validation operational
- Release candidate status achieved

## [6.0-sealed] — 2025-10-19
### Added
- Probabilistic Belief Propagation: Phase 6 complete
- Belief network convergence
- Sealed archive integrity
