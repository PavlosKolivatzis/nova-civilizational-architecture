# Nova Core Framework

## 🏗️ Overview

The `src/nova/` directory contains the core Nova Civilizational Architecture framework implementation. This is where the 10-slot cognitive system, Three Ledgers, and supporting infrastructure are implemented.

## 📁 Directory Structure

```
src/nova/
├── slots/              # 🧠 10 Cognitive Processing Slots (01-10)
│   ├── slot01_truth_anchor/          # Cryptographic reality verification
│   ├── slot02_deltathresh/           # Pattern detection & META_LENS
│   ├── slot03_emotional_matrix/      # Cognitive processing hub
│   ├── slot04_tri/                   # Flow-mesh reasoning engine
│   ├── slot05_constellation/         # Spatial navigation system
│   ├── slot06_cultural_synthesis/    # Ethical guardrails & synthesis
│   ├── slot07_production_controls/   # Circuit breaker & reflex system
│   ├── slot08_memory_ethics/         # ACL & self-healing memory
│   ├── slot09_distortion_protection/ # Hybrid defense system
│   └── slot10_civilizational_deployment/ # MetaLegitimacySeal
├── ledger/            # 📊 Three Ledgers System
│   ├── factory.py     # Ledger creation and management
│   ├── attest.py      # Attestation ledger
│   ├── claim.py       # Claim ledger
│   └── fact.py        # Fact ledger
├── ontology/          # 🧬 Mother Ontology v1.7.1
│   ├── loader.py      # Ontology loading and validation
│   ├── validator.py   # Contract validation
│   └── schemas/       # Ontology schemas
├── continuity/        # ⏰ Temporal Continuity Systems
│   ├── orp_hysteresis.py    # Operational Regime Policy
│   ├── temporal_consistency.py # Time-based consistency
│   └── avalon_ledger.py     # Autonomous Verification Ledger
└── core/              # 🔧 Core Infrastructure
    ├── config.py      # Configuration management
    ├── logging.py     # Structured logging
    └── utils/         # Shared utilities
```

## 🎯 Key Components

### Cognitive Slots (01-10)
Each slot represents a specialized cognitive function in the civilizational architecture:

- **Slot 1 (Truth Anchor)**: Cryptographic reality verification with autonomous recovery
- **Slot 2 (ΔTHRESH)**: Advanced pattern detection with META_LENS integration
- **Slot 3 (Emotional Matrix)**: Primary cognitive processing hub with 4 output contracts
- **Slot 4 (TRI Engine)**: Flow-mesh reasoning with drift detection
- **Slot 5 (Constellation)**: TRI-integrated spatial navigation system
- **Slot 6 (Cultural Synthesis)**: Ethical guardrails and anomaly unlearning
- **Slot 7 (Production Controls)**: Circuit breaker system with reflex coordination
- **Slot 8 (Memory Ethics)**: ACL protection with self-healing capabilities
- **Slot 9 (Distortion Protection)**: Multi-layer hybrid defense system
- **Slot 10 (Civilizational Deployment)**: MetaLegitimacySeal with autonomous rollback

### Three Ledgers System
The foundation of Nova's truth verification:
- **Fact Ledger**: Raw observations and measurements
- **Claim Ledger**: Processed interpretations and conclusions
- **Attest Ledger**: Cryptographic attestations and proofs

### Mother Ontology
Version 1.7.1 of the foundational conceptual framework that defines all system contracts and relationships.

## 🚀 Quick Start Examples

### Import Core Components
```python
# Import a cognitive slot
from nova.slots.slot01_truth_anchor import TruthAnchor

# Create ledger system
from nova.ledger.factory import create_ledger_system
ledgers = create_ledger_system()

# Load ontology
from nova.ontology.loader import load_mother_ontology
ontology = load_mother_ontology()
```

### Basic Slot Usage
```python
# Initialize a slot
from nova.slots.slot03_emotional_matrix import EmotionalMatrix
slot3 = EmotionalMatrix()

# Process cognitive input
result = slot3.process_cognitive_input(input_data)
```

## 🔗 Key Relationships

### Contract Network
```
Slot 3 → Slot 6 → Slot 10  (Emotional → Cultural → Deployment)
Slot 3 → Slot 4           (Emotional → TRI Processing)
Slot 6 → Slot 2           (Cultural → Threshold Management)
Slot 5 → Slot 9           (Constellation → Distortion Defense)
```

### Flow Fabric
Adaptive routing with real-time weight/frequency adjustment between slots.

### Reflex System
Upstream throttling and backpressure coordination through Slot 7.

## 📊 System Maturity

All components are at **Processual 4.0 maturity** with:
- Zero contract violations
- Autonomous recovery capabilities
- Comprehensive test coverage
- Production deployment readiness

## 🧪 Testing

Core framework tests are located in `tests/` with slot-specific test directories mirroring this structure.

## 📚 Related Documentation

- [Architecture Overview](../../docs/architecture/ARCHITECTURE.md)
- [Slot Contracts](../../contracts/)
- [Ontology Specification](../../docs/architecture/ontology/)
- [Three Ledgers Guide](../../docs/architecture/ledger/)

---

*This framework implements the complete Nova Civilizational Architecture for temporal intelligence and autonomous cognitive processing.*