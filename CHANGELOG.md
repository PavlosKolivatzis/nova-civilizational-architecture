# Changelog

All notable changes to Nova Civilizational Architecture will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Phase 14-1: PostgreSQL persistence with async writer
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
