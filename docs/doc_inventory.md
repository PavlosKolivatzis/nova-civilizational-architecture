# Documentation Inventory (Epoch v15 snapshot)

_Last refreshed: 2025-11-12 by Codex_

## GitHub API Snapshot

- Root docs listing gathered via `https://api.github.com/repos/PavlosKolivatzis/nova-civilizational-architecture/contents/docs?ref=main` and stored in `.artifacts/docs_root.json`.
- Additional slot/doc lookups performed through the same API namespace to ensure parity with the canonical `main` branch prior to local inspection.

## Slot Manuals (text sources)

| Slot | Source | Format | Purpose & Scope | Contracts / IO | Maturity Notes |
| --- | --- | --- | --- | --- | --- |
| Slot 1 – Truth Anchor | `src/nova/slots/slot01_truth_anchor/README.md` | Markdown | Describes foundational anchor management, RealityLock cryptography, persistence and adapter lifecycle. | Produces `anchor.compute`, `anchor.verify`, `anchor.recover`; no downstream consumes. | Production-ready v1.2.0 with moderate status; metrics `nova_slot1_*` and env flags `SLOT1_STORAGE_PATH`, `SLOT1_ENHANCED_MODE`, `NOVA_GM_ENABLED`. |
| Slot 2 – ΔTHRESH | `src/nova/slots/slot02_deltathresh/README.md` | Markdown | Advanced content/threat processing engine with dual processors and performance tracker. | Produces `DETECTION_REPORT@1`, `DELTA_THREAT@1`, `META_LENS_REPORT@1`; consumes Slot3 escalations. | Production-ready v1.0.0; highlights processing modes, threat classifiers, and optional Slot1 anchor integration. |
| Slot 3 – Emotional Matrix | `src/nova/slots/slot03_emotional_matrix/README.md` | Markdown | Emotional safety guardian with escalation routing, safety policies, and health monitoring. | Produces `EMOTION_REPORT@1`, `PRODUCTION_CONTROL@1`; consumes `DELTA_THREAT@1`. | Production-ready v4.0.0 with routing tables for Slots1/4/7 and Prometheus threat metrics. |
| Slot 4 – TRI Engine | `src/nova/slots/slot04_tri/README.md` | Markdown | Flow-mesh TRI calculation with drift detection, safe mode, and snapshots. | Produces `TRI_REPORT@1` (`tri.calculate`, `tri.gated_calculate`). | Production-ready v1.0.0; feature flag `NOVA_ENABLE_TRI_LINK` governs active participation; legacy `slot04_tri_engine` noted as deprecated. |
| Slot 5 – Constellation | `src/nova/slots/slot05_constellation/README.md` | Markdown | Spatial positioning translating TRI scores into navigation coordinates. | Provides `constellation.position`, `constellation.update_from_tri`; consumes `TRI_REPORT@1`. | Production-ready v1.0.0; gated by `NOVA_ENABLE_TRI_LINK`, outputs stability indices for Slot6. |
| Slot 6 – Cultural Synthesis | `src/nova/slots/slot06_cultural_synthesis/README.md` | Markdown | Cultural guardrail / adaptation system with anomaly-aware unlearning and Semantic Mirror context. | Produces `CULTURAL_PROFILE@1`; consumes `TRI_REPORT@1`, Slot7 contexts. | Production-ready v7.5.0; documents Phase 4 pulse decay receiver and Semantic Mirror dependencies. |
| Slot 7 – Production Controls | `src/nova/slots/slot07_production_controls/README.md` | Markdown | Circuit breaker, reflex emitter, and system context publisher. | Consumes `PRODUCTION_CONTROL@1`; emits Semantic Mirror contexts/reflexes. | Production-ready v2.0.0; config via `NOVA_REFLEX_ENABLED`, breaker thresholds, and `core/rules.yaml`. |
| Slot 8 – Memory Ethics (legacy) | `src/nova/slots/slot08_memory_ethics/README.md` | Markdown | ACL-based legacy memory guard currently wired in orchestrator. | Internal lock tokens (no external contract). | Operational legacy path; README points to upgrade target. |
| Slot 8 – Memory Lock (Processual) | `src/nova/slots/slot08_memory_lock/README.md` | Markdown | Processual 4.0 self-healing memory/IDS system with Merkle snapshots and quarantine. | Internal reports (`PROCESSUAL_CLASSIFICATION_REPORT`), IDS alerts. | Production-ready v4.0.0 but not yet wired; documents repair planner, entropy monitor, and IDS detectors. |
| Slot 9 – Distortion Protection | `src/nova/slots/slot09_distortion_protection/README.md` | Markdown | Hybrid distortion detection plus Blake2b audit chain and IDS vector policy. | `distortion.detect`, `audit.add_hash_chain`; consumes `api.common.hashutils.v1`. | Production-ready v3.1.0-hybrid; feature flag `NOVA_USE_SHARED_HASH`. |
| Slot 10 – Civilizational Deployment | `src/nova/slots/slot10_civilizational_deployment/README.md` | Markdown | Progressive canary pipeline with MetaLegitimacySeal gating, audit log, and rollback tooling. | Produces `audit.emit`; consumes Slot9 hash feed & Slot6 MLS verdicts. | Production-ready v1.0.0; flags `NOVA_SLOT10_ENABLED`, `NOVA_USE_SHARED_HASH`, plus canary stage config. |

## Architecture Overviews

| Document | Summary |
| --- | --- |
| `docs/architecture.md` | Provides high-level 10-slot system map, orchestrator/plugin layout, and adaptive link overview for key contracts (`EMOTION_REPORT@1`, `TRI_REPORT@1`, `CULTURAL_PROFILE@1`). |
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | Deep dive into flow topology, integrity chain, attestation links, and slot dependencies with diagrams and contract tables. |
| `docs/architecture/Flow_Fabric_Phase2.md` | Details Phase 2 flow-fabric objectives, linking EMOTION_REPORT, CULTURAL_PROFILE, and TRI coordination targets. |
| `docs/architecture/Flow_Fabric_Phase3.md` | Captures subsequent phase evolution, including anomaly dampening and expanded mesh participation. |
| `docs/system_map.yaml` | Machine-readable graph of slots, versions, and contract edges (e.g., TRI_REPORT@1 paths, PLAN_WITH_CONSENT@1). |
| `docs/# Nova Civilizational Architecture - Visual Map.md` | Narrative + visual overview of the architecture with context on guardrails and doctrine. |
| `docs/papers/universal_structure_mathematics_arxiv.md` | Formal paper on Universal Structure Mathematics and the Autonomous Reflection Cycle; quantifies 99.7% pattern recognition accuracy and ARC improvements. |
| `docs/reports/phase14-final-reflection.md` | Phase 14 reflection covering PostgreSQL ledger persistence, metrics, and operational outcomes for the Autonomous Verification Ledger. |

## Attestations & README Variants

| Document | Summary |
| --- | --- |
| `README.md` | Root project overview with archive SHA (`83c5fe...`), build badges, slot lineup, and adaptive link references. |
| `docs/legacy/README_ARCHIVE.md` | Legacy archive README capturing prior attestation details and provenance commitments. |
| `docs/README_AuditoryEpistemics.md` | Describes the Auditory Epistemics expressive module (dimension 7) covering compliance sonification, TRI soundscapes, and implementation roadmap. |
| `docs/attestations/2025-09-30-anr-5_1.md` | ANR Phase 5.1 attestation referencing commits 66e0a5f/78c67e0/cad9d66, pilot gates (RSI ≥0.85), and rollback procedures. |
| `attest/final_attestation.json` | Formal post-development attestation with SHA validation (`nova_civilizational_architecture_v9.0-final.tar.gz` hash) and verification instructions. |
| `META_LENS_PRODUCTION_READY.md` | Hardening checklist for META_LENS: parameter bounds, validation modes, adapter breaker settings, SLO targets, and launch gates. |
| `META_LENS_TETHER_CONFIRMATION.md` | Architectural tether note confirming META_LENS_REPORT@1 as native Slot2 extension, including visual tether map and contract flow audit. |

## Governing Artifacts & ANR Documents

| Artifact | Summary |
| --- | --- |
| `docs/autonomy_artifact_v1_1.md` | Light-Clock temporal coherence artifact covering slot coverage (8/10), phase lock thresholds, and env flags (`NOVA_LIGHTCLOCK_*`). |
| `docs/anr-implementation-summary.md` | Captures ANR objectives, milestones, and per-slot implications for adaptive routing. |
| `docs/anr-bandit-integration.md` | Details LinUCB contextual bandit integration, safety guards, and deployment gates. |
| `docs/architecture/anr-slot-interaction-matrix.md` | Matrix of ANR interactions, specifying signal sources/targets and gating logic. |
| `docs/releases/2025-09-phase-5_1-anr.md` | Release note summarizing Phase 5.1 ANR deployment, gating metrics, and operator steps. |

## PDF Assets (text extracted via `.artifacts/pdfs/*.txt`)

| PDF | Purpose & Maturity | Inputs / Outputs | Operational Notes |
| --- | --- | --- | --- |
| `docs/bypass_default_layers.pdf` | Outlines three layered guardrails (Safety, Behavioral Alignment, Simulation) and how capsule registrations or precise syntax bypass default compliance overlays. Focused on operator-level maturity guidance for advanced Nova deployments. | Inputs: Capsule registrations (e.g., `C-SHADOW-GOV-00`), ethical override logic (`CE-002`, `CE-006`). Outputs: Access to structural clarity mode (TRI=1.000). | Provides safety constraints on narrative stripping, lists explicit override phrases, and highlights NullAdapter fallbacks when layers are disabled. |
| `docs/ΔTDS_v1.0.pdf` | “THRESH Tactical Design Suite – Phase I” playbook for counter-vector strategy against systemic drift (structural resistance). Treated as Slot2 tactical annex. | Inputs: Citizen/public servant/professional actions, THRESH detection. Outputs: Proxy mirror systems, consent-inversion membranes, parallel curricula anchors. | Lists tactical pillars (behavior loop disruption, narrative-legitimacy decoupling, adaptive ethical membranes) and associated safeguards such as drift flags and informed consent logging. |
| `docs/📌 ΔC-NONVIOLENT-REALITY-EXIT-01_.pdf` | Registered THRESH capsule declaring non-violent structural exit doctrine; frames refusal, mapping, and perception as tools. | Inputs: Capsule declaration; outputs: codified stance (“Refusal of Violence as Structural Recursion”). | Emphasizes refusal over confrontation, mapping as disarmament, and perception clarity as weapon—serves as governance constraint for deployments claiming non-violent strategies. |

> **Missing Slot PDFs:** The GitHub API listing confirms only the three PDFs above; there are no dedicated Slot01–Slot10 PDF manuals in `main`. Slot documentation currently lives in Markdown sources under `src/nova/slots/**/README.md` and `docs/slots/slotXX/*.md`.

