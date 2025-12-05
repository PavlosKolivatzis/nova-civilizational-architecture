# Nova Civilizational Architecture - Glossary

## 📚 Core Terms and Concepts

This glossary provides definitions for key terms, concepts, and components in the Nova Civilizational Architecture system.

---

## A

**ADR (Architectural Decision Record)**
- A document that captures an important architectural decision along with its context and consequences
- Location: `docs/architecture/adr/`

**ANR (Adaptive Neural Routing)**
- A system component for intelligent routing and adaptation
- Used in phase implementations for flexible decision making

**Attestation**
- A cryptographic or logical proof of system state or compliance
- Part of the Three Ledgers system

**AVL (Autonomous Verification Ledger)**
- Meta-proof layer for regime-level truth and temporal continuity
- Captures pre-transition state snapshots with hash chain immutability
- **[Mother Ontology §5.1]**

---

## B

**Belief State**
- The current computational representation of beliefs and assumptions in the system
- Managed through slot-based architecture

---

## C

**Canon (Canonical Documentation)**
- The authoritative, officially recognized documentation set
- Defined in `docs/architecture/ontology/_canon.yaml`

**Civilizational Architecture**
- The overarching system design for managing complex societal-scale information processing
- The primary focus of this project

**Checkpoint**
- Phase 14.2 Merkle tree commitment for temporal continuity verification
- ACID-compliant persistence point in PostgreSQL ledger storage

**Compaction**
- Phase 14.2 process for optimizing historical ledger data storage
- Reduces storage overhead while maintaining temporal consistency

**Contract**
- A formal specification defining the interface and behavior of system components
- Location: `contracts/`

**CSI (Cognitive State Interface)**
- The interface for managing cognitive states within slots

---

## D

**Delta Threshold**
- A mechanism for detecting significant changes in system state
- Critical for regime transitions

**Distortion Detection**
- System for identifying and handling information distortion
- Part of the distortion protection slot (Slot 9)

**Drift Guard**
- Phase 13b mechanism for preventing temporal drift during regime transitions
- Monitors consistency bounds and triggers continuity preservation

**Dual-Modality Verification**
- Phase 13b verification combining ORP hysteresis with oracle consensus
- Ensures regime transition validity through multiple independent channels

---

## E

**EPOCH**
- A temporal boundary marker for system phases and releases
- Current: EPOCH V10 (manifest in `docs/research/manifests/`)

---

## F

**Fact Ledger**
- One of the Three Ledgers, containing raw observations and measurements
- See: Claim Ledger, Attest Ledger

---

## G

**Governance**
- The system of rules, practices, and processes for directing and controlling the architecture
- Managed through wisdom governor components

---

## H

**Hysteresis**
- A property of systems where the output depends not only on the current input but also on the history of inputs
- Used in decision-making loops

---

## I

**Interface**
- A defined boundary between system components
- Contracts specify interfaces between slots and external systems

**Invariance**
- Properties that remain constant under system transformations
- Critical for maintaining system stability

---

## L

**Ledger System (Three Ledgers)**
- **Fact Ledger**: Raw observations and data
- **Claim Ledger**: Processed interpretations and conclusions
- **Attest Ledger**: Attestations and proofs of compliance

**Legacy Systems**
- Older system components that have been superseded but may still be referenced
- Location: `docs/archive/legacy/`

**Lifecycle Status**
- Metadata indicating the current status of documentation or components
- ACTIVE, DEPRECATED, ARCHIVED, UNDER_DEVELOPMENT

---

## M

**Meta Lens**
- A system for monitoring and analyzing the architecture itself
- Includes production readiness assessments

**Mother Ontology**
- The foundational ontology defining the system's conceptual framework
- Current version: v1.7.1

**Ontology Meta-Terms**
- **Invariance Matrix** - Properties preserved across system transformations **[Ontology §1.2]**
- **Dependency Graph** - Component relationship network **[Ontology §1.3]**
- **Processual Maturity** - 4.0-level autonomous operation standards **[Ontology §1.4]**
- **Temporal Bounds** - Acceptable consistency limits for time-based operations **[Ontology §2.3]**
- **Contract Schema** - Formal interface specifications between components **[Ontology §3.1]**
- **Flow Constraints** - Routing and communication limitations **[Ontology §6.1]**

---

## N

**Nova Framework**
- The core software framework implementing the civilizational architecture
- Location: `src/nova/`

**Nova AI Operating Framework**
- Guidelines and principles for AI system operation within the architecture
- Location: `agents/nova_ai_operating_framework.md`

---

## O

**Ontology**
- The formal specification of concepts, relationships, and constraints in the system
- Current: Mother Ontology v1.7.1

**Oracle Context**
- Phase 13b external verification source for regime transition validation
- Provides independent consensus for dual-modality verification

**ORP (Operational Resilience Protocol)**
- System for maintaining operational stability during disruptions
- Critical for regime transition management

**Orphaned Document**
- A document not properly categorized in the canonical structure
- Identified and managed through the Sunlight Scanner

---

## P

**Phase**
- A major development stage in the system's evolution
- Current: Phase 14-0 (Repository Consolidation)

**Predictive Consistency**
- System for maintaining coherent predictions across time
- Prevents temporal contradictions

**Pre-transition Regime**
- Phase 13b state captured by temporal snapshots before regime changes
- Ensures zero data loss during hysteresis-based transitions

---

## R

**Regime**
- A distinct operational state of the system
- Transitions between regimes are managed through hysteresis

**Regime Transition**
- The process of moving from one operational regime to another
- Governed by stability protocols

**Root Mode**
- The fundamental operational mode of the system
- Alternative to derived or specialized modes

---

## S

**Slot System**
- The architectural pattern of dividing functionality into discrete, manageable components
- Slots 01-10 cover truth, emotion, production, memory, etc.

**Slot Definitions (01-10)**
- **Slot 01: Truth Anchor** - Cryptographic reality verification with autonomous recovery **[Ontology §2.1]**
- **Slot 02: ΔTHRESH** - Advanced pattern detection with META_LENS integration **[Ontology §2.2]**
- **Slot 03: Emotional Matrix** - Primary cognitive processing hub with 4 output contracts **[Ontology §3.4]**
- **Slot 04: TRI Engine** - Flow-mesh reasoning with drift detection **[Ontology §4.1]**
- **Slot 05: Constellation** - TRI-integrated spatial navigation system **[Ontology §4.2]**
- **Slot 06: Cultural Synthesis** - Ethical guardrails and anomaly unlearning **[Ontology §5.3]**
- **Slot 07: Production Controls** - Circuit breaker system with reflex coordination **[Ontology §6.2]**
- **Slot 08: Memory Ethics** - ACL protection with self-healing capabilities **[Ontology §7.1]**
- **Slot 09: Distortion Protection** - Multi-layer hybrid defense system **[Ontology §8.2]**
- **Slot 10: Civilizational Deployment** - MetaLegitimacySeal with autonomous rollback **[Ontology §9.1]**

**Sunlight Doctrine**
- The documentation principle: Observe → Canonize → Attest → Publish
- Ensures transparency and traceability

**Serializable Isolation**
- Phase 14.2 PostgreSQL transaction isolation level ensuring temporal consistency
- Prevents anomalies in concurrent ledger operations

**Snapshot**
- Phase 13b immutable capture of system state before regime transitions
- Deterministic serialization with hash chain immutability

**Sunlight Scanner**
- Automated tool for validating document lifecycle status and canon compliance
- Location: `scripts/maintenance/sunlight_scan.py`

---

## T

**Temporal Consistency**
- The property of maintaining coherent state across time
- Critical for predictive systems

**Three Ledgers**
- See: Ledger System (Fact, Claim, Attest)

**Truth Anchor**
- The fundamental mechanism for establishing and maintaining truth
- Slot 1 in the system

**Tri-Truth Signal**
- A mechanism for identifying and validating truth through multiple channels
- Part of the tri-state verification system

**Trust Windows**
- Phase 14.2 configurable time periods for temporal consistency validation
- Define acceptable bounds for historical data verification

---

## U

**URF (Universal Reference Framework)**
- The overarching framework for organizing and referencing system components
- Provides consistency across modules

---

## W

**Wisdom Governor**
- The system component responsible for implementing governance decisions
- Manages the balance between efficiency and wisdom

---

## Z

**Zero-Knowledge**
- Privacy-preserving verification without revealing underlying information
- Used in attestation systems

---

## Common File Patterns

### File Extensions
- `.md`: Markdown documentation
- `.yaml`: Configuration and specification files
- `.py`: Python source code
- `.yml`: Alternative YAML extension

### Directory Patterns
- `docs/`: All documentation
- `src/nova/`: Core framework code
- `tests/`: Test suite
- `contracts/`: System contracts
- `scripts/`: Maintenance and utility scripts
- `ops/`: Operations and monitoring

### Versioning
- Semantic versioning for contracts (e.g., `slot06_cultural@2.yaml`)
- Ontology versions (e.g., Mother Ontology v1.7.1)
- Phase versions (e.g., Phase 14-0)

---

## Related Concepts

**System Maturity**
- The overall readiness and stability of the system
- Documented in `docs/architecture/system_maturity.yaml`

**Test Coverage**
- Comprehensive testing strategy with 2021 tests passing (2117 collected)
- Coverage metrics in `docs/architecture/SYSTEM_ANALYSIS.md`

**Dependency Graph**
- The network of component dependencies
- Documented in `docs/architecture/Nova_Dependency_Graph_v1.7.1.yaml`

---

*This glossary is maintained as part of the Phase 14-0 Repository Consolidation initiative. For the most current definitions, see `docs/architecture/ontology/` for technical specifications.*