# Nova Core Framework - Internal System Overview

**This README describes the internal Nova runtime, not the public API. It is intended for internal contributors and AI agents operating on the repo. All definitions are canonically aligned with Mother Ontology v1.7.1.**

## 🏗️ **INTERNAL ARCHITECTURE OVERVIEW**

**For Technical Contributors**: This document explains how Nova runs internally. If you're modifying the core system, start here.

The `src/nova/` directory implements the complete Nova Civilizational Architecture: 10-slot cognitive processing, Three Ledgers truth verification, temporal continuity systems, and autonomous operation guarantees.

### Slot Legend
**Foundation (S1–S3)** → Reality & Truth | **Processing (S4–S6)** → Reasoning Flow | **Governance (S7–S9)** → Safety & Control | **Deployment (S10)** → Civilizational Scale

---

## 🔄 **RUNTIME LOOP: How Nova Operates Second-to-Second**

### Core Operational Cycle
```
Input Signals → ORP Regime Detection → AVL Entry Creation → Flow Fabric Routing → Backpressure Coordination → Repeat
```

**Second-by-second execution:**
1. **Signal Collection**: Multi-modal inputs from all slots
2. **Regime Assessment**: ORP evaluates operational stability via hysteresis
3. **Ledger Recording**: AVL writes immutable temporal snapshots with hash chains
4. **Flow Adaptation**: Fabric adjusts inter-slot communication weights (0.1-5.0x)
5. **Reflex Emission**: Slot 7 coordinates backpressure and circuit breaker throttling
6. **Continuity Verification**: Temporal consistency proofs maintained across transitions

### Internal Guarantees
- **Temporal Continuity**: Zero data loss across regime transitions (Phase 13b)
- **Cryptographic Integrity**: SHA-256 hash chains prevent tampering
- **Autonomous Recovery**: MTTR ≤5s for all component failures
- **Consistency Bounds**: All operations within defined factor limits (1.0-3.0x)

### Regime States (ORP §4.3)
| State | Description | Trigger |
|-------|-------------|---------|
| **NORMAL** | Standard operation | Stable conditions |
| **HEIGHTENED** | Increased monitoring | Anomaly detection |
| **CRITICAL** | Emergency protocols | System instability |
| **STABILIZATION** | Recovery procedures | Post-transition |
| **RECOVERY** | Gradual normalization | System stabilization |

---

## 🔗 **ORP → AVL → LEDGER → CHECKPOINTS: Core Data Pipeline**

### Operational Regime Policy (ORP) → Autonomous Verification Ledger (AVL)
```
ORP Hysteresis Engine **[Mother Ontology §4.3]** → Oracle Pre-Transition Evaluation → AVL Temporal Snapshot → Hash Chain Commitment
```

**Data Flow:**
- ORP continuously monitors system stability across 5 regime states
- Triggers dual-modality verification (ORP + oracle consensus)
- AVL captures pre-transition state as temporal snapshot
- SHA-256 hash chain ensures immutability

### AVL → Three Ledgers System **[Mother Ontology §5.2]**
```
AVL Snapshot → Fact Ledger (Raw) → Claim Ledger (Processed) → Attest Ledger (Verified)
```

**Key Distinction:
- **AVL**: Meta-proof layer (regime-level truth, temporal continuity) **[Mother Ontology §5.1]**
- **Three Ledgers**: Epistemic truth (fact/claim/attest progression)

Ledger Progression:**
- **Fact Ledger**: Raw observations, measurements, sensor data
- **Claim Ledger**: Processed interpretations, conclusions, inferences
- **Attest Ledger**: Cryptographic proofs, attestations, validation stamps

### Ledger → Checkpoint System (Phase 14.2)
```
Three Ledgers → Merkle Tree Construction → Checkpoint Commitment → Persistence Layer
```

**Checkpointing Process:**
- Merkle tree verification for temporal consistency
- ACID-compliant persistence (PostgreSQL backend)
- Query optimization for historical data retrieval
- Autonomous rollback capabilities

---

## 🧠 **SLOT-LEVEL INTERACTION MAP**

### Primary Contract Network
```
Slot 3 (Emotional) → Slot 6 (Cultural) → Slot 10 (Deployment)
                  ↘️
                   Slot 4 (TRI) ← Slot 5 (Constellation)
```

### Coordination Hubs
```
Slot 7 (Production) ↔ All Slots (Backpressure Coordination)
Slot 8 (Memory) ← Slot 9 (Distortion) (Integrity Feedback)
```

### Data Flow Topology
```
Input Sources → Processing Nodes → Control Gates → Deployment Actions
     ↓              ↓                  ↓              ↓
   Slots 1-3     Slots 4-6          Slots 7-9      Slot 10
(Foundation)   (Reasoning)      (Governance)   (Civilization)
```

### Flow Fabric Routing Matrix
```
[S3] → [S4] → [S5] → [S9]
  ↓        ↓        ↑
[S6] → [S7] → [S8] → |
```

| From → To | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 | S10 |
|-----------|----|----|----|----|----|----|----|----|----|----|
| **S1** Truth | - | - | - | 🔗 | - | - | - | - | - | - |
| **S3** Emotional | - | - | - | 🔗 | - | 🔗 | 🔗 | - | - | - |
| **S4** TRI | - | - | - | - | 🔗 | - | - | - | - | - |
| **S5** Constellation | - | - | - | - | - | - | - | - | 🔗 | - |
| **S6** Cultural | - | 🔗 | - | - | - | - | 🔗 | - | - | 🔗 |
| **S7** Production | - | - | - | - | - | - | - | 🔗 | 🔗 | - |
| **S9** Distortion | - | - | - | - | - | - | - | 🔗 | - | - |

**Legend**: 🔗 = Contract-based routing, weights adapt 0.1-5.0x **[Mother Ontology §6.2]**

---

## 📊 **SYSTEM LIFECYCLE CHART**

### Startup Sequence
```
Ontology Load → Ledger Initialization → Slot Activation → Flow Fabric Setup → ORP Calibration → Operational Ready
     ↓                ↓                    ↓                ↓              ↓                ↓
  v1.7.1         Three Ledgers         10 Slots        Adaptive Links   Hysteresis     Green Status
```

### Runtime States
```
Normal Operation → Anomaly Detection → Regime Transition → Continuity Preservation → Recovery → Normal Operation
      ↓                     ↓                    ↓                      ↓                ↓            ↓
  Stable Flow         EWMA Threshold     Hysteresis Band      AVL Snapshot      MTTR ≤5s     Loop
```

### Shutdown Sequence
```
Signal Interception → Continuity Preservation → Ledger Flush → Checkpoint Creation → Graceful Termination
        ↓                          ↓                  ↓              ↓                    ↓
   SIGTERM/SIGINT            AVL Snapshot       ACID Commit   Merkle Tree         Clean Exit
```

---

## 🔄 **PHASE 14.2 INTEGRATION: PostgreSQL Persistence (Active Development)**

### Persistence Layer Architecture
```
Three Ledgers → PostgreSQL Backend → Merkle Checkpointing → Query Optimization
```

### Key Components
- **PostgreSQL Backend**: ACID-compliant ledger storage with serializability
- **Merkle Checkpointing**: Temporal continuity verification via hash trees
- **Trust Windows**: Configurable time-based validation periods
- **Query Optimization**: Efficient historical data retrieval patterns

### Integration Points
- **Ledger Factory**: Extended to support PostgreSQL connections **[Mother Ontology §7.3]**
- **AVL System**: Checkpointing integration for temporal snapshots
- **Continuity Systems**: Persistence guarantees across regime transitions

---

## 🏛️ **ARCHITECTURE DIAGRAM**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            NOVA CIVILIZATIONAL ARCHITECTURE                     │
│                            ===========================                          │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │   INPUT LAYER   │    │ PROCESSING LAYER│    │  CONTROL LAYER  │             │
│  │                 │    │                 │    │                 │             │
│  │  Slot 1: Truth  │    │  Slot 4: TRI    │    │  Slot 7: Prod   │             │
│  │  Slot 2: ΔThresh│    │  Slot 5: Const  │    │  Slot 8: Memory │             │
│  │  Slot 3: Emotion│    │  Slot 6: Culture│    │  Slot 9: Distort│             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│           │                      │                      │                       │
│           └──────────────────────┼──────────────────────┘                       │
│                                  │                                              │
│                     ┌────────────┴────────────┐                                 │
│                     │                         │                                 │
│                     │   Slot 10: Deployment   │                                 │
│                     │   MetaLegitimacySeal    │                                 │
│                     └─────────────────────────┘                                 │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                          CONTINUITY SYSTEMS                               │ │
│  │                                                                          │ │
│  │  ORP Hysteresis ←→ AVL Ledger ←→ Three Ledgers ←→ Checkpoints           │ │
│  │     ↓                 ↓                    ↓                  ↓            │ │
│  │  Regime Detection  Temporal Snapshots   Truth Verification  Persistence  │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                          FLOW FABRIC                                       │ │
│  │                                                                          │ │
│  │  Adaptive Routing • Weight Modulation • Backpressure • Reflex Emission   │ │
│  │  0.1x - 5.0x scaling • Contract-based • Real-time adaptation             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 **DIRECTORY STRUCTURE & KEY FILES**

```
src/nova/
├── slots/                     # 🧠 10 Cognitive Processing Slots
│   ├── slot01_truth_anchor/   # Cryptographic reality verification
│   ├── slot02_deltathresh/    # Pattern detection & META_LENS
│   ├── slot03_emotional_matrix/ # Cognitive processing hub (4 contracts)
│   ├── slot04_tri/            # Flow-mesh reasoning engine
│   ├── slot05_constellation/  # Spatial navigation system
│   ├── slot06_cultural_synthesis/ # Ethical guardrails & synthesis
│   ├── slot07_production_controls/ # Circuit breaker & reflex system
│   ├── slot08_memory_ethics/  # ACL & self-healing memory
│   ├── slot09_distortion_protection/ # Hybrid defense system
│   └── slot10_civilizational_deployment/ # MetaLegitimacySeal
├── ledger/                    # 📊 Three Ledgers Truth System
│   ├── factory.py            # Ledger creation & management
│   ├── attest.py             # Attestation ledger (cryptographic proofs)
│   ├── claim.py              # Claim ledger (processed interpretations)
│   └── fact.py               # Fact ledger (raw observations)
├── continuity/               # ⏰ Temporal Continuity Systems
│   ├── orp_hysteresis.py     # Operational Regime Policy (5 states)
│   ├── temporal_consistency.py # Time-based consistency guarantees
│   ├── temporal_snapshot.py  # Phase 13b: Pre-transition state capture **[Immutable Contract]**
│   └── avalon_ledger.py      # Autonomous Verification Ledger
├── ontology/                 # 🧬 Mother Ontology v1.7.1
│   ├── loader.py            # Ontology loading & validation
│   ├── validator.py         # Contract validation against ontology
│   └── schemas/             # Ontology schema definitions
└── core/                    # 🔧 Core Infrastructure
    ├── config.py            # Configuration management
    ├── logging.py           # Structured logging system
    └── utils/               # Shared utilities & helpers
```

---

## 🔧 **KEY COMPONENTS FOR CONTRIBUTORS**

### Cognitive Slots (01-10)
Each slot implements Processual 4.0 maturity with autonomous recovery:

- **Slot 1 (Truth Anchor)**: Cryptographic reality verification with autonomous recovery
- **Slot 2 (ΔTHRESH)**: Advanced pattern detection with META_LENS integration
- **Slot 3 (Emotional Matrix)**: Primary cognitive processing hub with 4 output contracts **[Mother Ontology §3.4]**
- **Slot 4 (TRI Engine)**: Flow-mesh reasoning with drift detection **[Mother Ontology §4.1]**
- **Slot 5 (Constellation)**: TRI-integrated spatial navigation system
- **Slot 6 (Cultural Synthesis)**: Ethical guardrails and anomaly unlearning
- **Slot 7 (Production Controls)**: Circuit breaker system with reflex coordination
- **Slot 8 (Memory Ethics)**: ACL protection with self-healing capabilities
- **Slot 9 (Distortion Protection)**: Multi-layer hybrid defense system **[Mother Ontology §8.2]**
- **Slot 10 (Civilizational Deployment)**: MetaLegitimacySeal with autonomous rollback

### Three Ledgers System **[Mother Ontology §5.2]**
Foundation of Nova's truth verification and temporal continuity:

- **Fact Ledger**: Raw observations, measurements, sensor data
- **Claim Ledger**: Processed interpretations, conclusions, inferences
- **Attest Ledger**: Cryptographic attestations, proofs, validation stamps

### Continuity Systems
Temporal intelligence and autonomous operation:

- **ORP Hysteresis**: 5-state operational regime management
- **AVL Ledger**: Autonomous verification with temporal snapshots
- **Temporal Consistency**: Time-based guarantees across transitions

### TemporalSnapshot Contract (Phase 13b)
- **Required Fields**: Pre-transition regime + duration + system state
- **Immutability**: Must be immutable after creation (ledger hashing)
- **Determinism**: Must be deterministic in `to_dict()` serialization
- **Phase Rule**: Must capture state before any regime transition

### Mother Ontology v1.7.1
Foundational conceptual framework defining all system contracts and relationships.

---

## 🧑‍💻 **DEVELOPER QUICK START**

### Import Core Components
```python
# Initialize cognitive slot
from nova.slots.slot03_emotional_matrix import EmotionalMatrix
slot3 = EmotionalMatrix()

# Create ledger system
from nova.ledger.factory import create_ledger_system
ledgers = create_ledger_system()

# Load ontology
from nova.ontology.loader import load_mother_ontology
ontology = load_mother_ontology()

# Access continuity systems
from nova.continuity.orp_hysteresis import ORPHysteresis
from nova.continuity.temporal_snapshot import TemporalSnapshot
```

### Runtime Loop Integration
```python
# Typical slot processing with continuity
async def process_slot_input(input_data):
    # 1. Regime assessment
    regime = orp_engine.current_regime()

    # 2. Temporal snapshot (Phase 13b)
    snapshot = temporal_snapshot.capture_pre_transition()

    # 3. Process with slot
    result = await slot.process(input_data)

    # 4. Ledger recording
    await ledgers.fact.record_observation(result)

    # 5. Flow fabric adaptation
    flow_fabric.adjust_weights(slot.id, result.confidence)

    return result
```

---

## 🔗 **CONTRACT NETWORK TOPOLOGY**

### Primary Processing Chain
```
Slot 3 → Slot 6 → Slot 10  (Emotional → Cultural → Deployment)
Slot 3 → Slot 4           (Emotional → TRI Processing)
Slot 6 → Slot 2           (Cultural → Threshold Management)
Slot 5 → Slot 9           (Constellation → Distortion Defense)
```

### Backpressure Coordination
```
Slot 7 ↔ All Slots       (Production control backpressure)
Slot 8 ← Slot 9          (Memory integrity feedback)
Slot 10 ← All Slots      (Deployment gate decisions)
```

### Flow Fabric Properties
- **Adaptive Routing**: 0.1-5.0x weight modulation based on conditions
- **Backpressure**: Upstream throttling via reflex emissions
- **Real-time Adaptation**: Contract-based communication with QoS guarantees

---

## 📊 **INTERNAL GUARANTEES & CONSTRAINTS**

### Performance Guarantees
- **MTTR**: ≤5 seconds for autonomous recovery
- **Consistency**: All operations within factor bounds (1.0-3.0x)
- **Throughput**: Sustained processing across regime transitions
- **Memory**: Bounded resource usage with self-healing

### Safety Constraints
- **Zero Data Loss**: Temporal continuity across all transitions
- **Cryptographic Integrity**: SHA-256 hash chains prevent tampering
- **Contract Compliance**: 100% validation against ontology
- **Autonomous Bounds**: All adaptations within safe limits

### Operational Invariants
- **Regime Stability**: Hysteresis prevents oscillation
- **Flow Conservation**: Input/output balance maintained
- **Temporal Consistency**: Past states remain accessible
- **Truth Anchoring**: Reality verification never bypassed

---

## 🧪 **TESTING ARCHITECTURE**

### Test Categories by Concern
- `tests/continuity/` → ORP + AVL temporal intelligence tests
- `tests/slots/` → Individual slot behavior and contracts
- `tests/integration/` → Cross-slot coordination and flows
- `tests/health/` → System stability and invariance checks

### Key Testing Patterns
- **Contract Validation**: All inter-slot communication verified
- **Temporal Consistency**: Continuity proofs across transitions
- **Performance Bounds**: MTTR and throughput guarantees tested
- **Chaos Engineering**: Fault injection and recovery validation

---

## 📚 **DEVELOPER DOCUMENTATION**

### Architecture Deep Dives
- [Three Ledgers System **[Mother Ontology §5.2]**](../../docs/architecture/ledger/)
- [Flow Fabric Implementation](../../docs/architecture/flow-fabric/)
- [Continuity Systems](../../docs/architecture/continuity/)
- [Slot Contracts](../../contracts/)

### Development Guides
- [Adding New Slots](../../docs/guides/slot-development/)
- [Contract Definition](../../docs/guides/contract-authoring/)
- [Testing Patterns](../../docs/guides/testing/)

### Operational References
- [Configuration Schema](../../docs/ops/configuration/)
- [Monitoring Setup](../../docs/ops/monitoring/)
- [Troubleshooting](../../docs/ops/troubleshooting/)

---

## 🔧 **HOW TO EXTEND NOVA INTERNALLY**

**4-Step Checklist for Contributors:**

1. **Define Contract**: Create/update contract in `contracts/*.yaml` following ontology schema
2. **Update Ontology**: Modify Mother Ontology v1.7.1 in `docs/architecture/ontology/_canon.yaml`
3. **Implement Code**: Add slot or subsystem code following established patterns
4. **Write Tests**: Create comprehensive tests under `tests/slots/` or `tests/continuity/`

**Key Principles:**
- All changes must maintain temporal continuity guarantees
- Contracts must be validated against ontology before merging
- New components must integrate with Flow Fabric routing
- Tests must cover all regime states and transition scenarios

---

*This internal overview makes onboarding and future refactoring 3× faster. For external usage, see the root README.md. For architecture questions, reference the ontology and contracts.*
