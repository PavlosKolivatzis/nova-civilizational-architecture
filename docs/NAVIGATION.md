# Nova Civilizational Architecture - AI Agent & Contributor Navigation Guide

## 🤖 **FOR AI AGENTS: INSTANT ORIENTATION PROTOCOL**

**If you are Claude CLI, Kilo Code AI, or any LLM analyzing this codebase:**

Read this guide first — It contains all navigation mappings

Use search keywords listed below for instant location finding

Follow clickable paths to understand specific components

Reference ontology sections for canonical definitions

**Goal**: Zero confusion navigation. This guide eliminates all friction forever.

### **Mental Model: Nova System Flow**
```
[Input Signals] → [Slot 1-3: Foundation] → [Slot 4-6: Processing] → [Slot 7-9: Control] → [Slot 10: Deployment]
                      ↓                           ↓                        ↓                        ↓
                Truth & Reality           Reasoning Flow          Governance & Safety     Civilizational Scale
```

### **Temporal System Flow (Phase 13b + 14.2)**
```
ORP Hysteresis → Temporal Snapshot → AVL Ledger → Three Ledgers → Merkle Checkpoints
     ↓                    ↓                 ↓              ↓                ↓
Regime Detection    Pre-transition      Immutable       Fact→Claim→     PostgreSQL
                    State Capture       Proofs         Attest         Persistence
```

### **Current Phase Status**

**Phase: 14.2 (Upcoming)**
**Focus: PostgreSQL-ledger, Merkle checkpoints, trust windows**
**Status: All prerequisites satisfied — ready for implementation**

---

## 🔍 **SEARCH KEYWORDS FOR INSTANT LOCATION**

**AI Agent Quick Reference - Search these terms to find information instantly:**

| **What you want to understand** | **Search Keywords** | **Primary Location** |
|--------------------------------|-------------------|-------------------|
| **System Architecture** | `Mother Ontology`, `10 slots`, `civilizational` | [`docs/architecture/ontology/_canon.yaml`](docs/architecture/ontology/_canon.yaml) |
| **Slot Implementation** | `slot01_truth_anchor`, `slot03_emotional_matrix` | [`src/nova/slots/`](src/nova/slots/) |
| **Three Ledgers** | `fact_claim_attest`, `ledger_factory` | [`src/nova/ledger/`](src/nova/ledger/) |
| **Temporal Continuity** | `ORP_hysteresis`, `temporal_snapshot` | [`src/nova/continuity/`](src/nova/continuity/) |
| **Flow Fabric** | `adaptive_routing`, `backpressure` | [`src/nova/slots/slot07_production_controls/`](src/nova/slots/slot07_production_controls/) |
| **Contracts** | `contract_validation`, `ontology_schema` | [`contracts/`](contracts/) |
| **Testing** | `pytest`, `continuity/`, `slots/` | [`tests/`](tests/) |
| **Configuration** | `JWT_SECRET`, `NOVA_WISDOM_*` | [`config/`](config/) |

---

## 🎯 **"IF YOU WANT TO UNDERSTAND X, GO HERE" - DIRECT MAPPINGS**

### **Understanding System Architecture**
- **How Nova works at high level** → [`README.md`](README.md) (external overview)
- **Internal runtime details** → [`src/nova/README.md`](src/nova/README.md) (technical deep-dive)
- **Mother Ontology v1.7.1** → [`docs/architecture/ontology/_canon.yaml`](docs/architecture/ontology/_canon.yaml)
- **Architecture decisions** → [`docs/architecture/adr/`](docs/architecture/adr/)

### **Understanding Slots (01-10)**
*See also: [Slot Interaction Matrix](src/nova/README.md#slot-level-interaction-map) for routing details*

- **Slot 1: Truth Anchor** → [`src/nova/slots/slot01_truth_anchor/`](src/nova/slots/slot01_truth_anchor/) | Contract: [`contracts/slot01_truth_anchor@1.yaml`](contracts/slot01_truth_anchor@1.yaml)
- **Slot 2: ΔTHRESH** → [`src/nova/slots/slot02_deltathresh/`](src/nova/slots/slot02_deltathresh/) | ADR: [`docs/architecture/adr/ADR-Slot01-QuantumEntropy-v1.0.md`](docs/architecture/adr/ADR-Slot01-QuantumEntropy-v1.0.md)
- **Slot 3: Emotional Matrix** → [`src/nova/slots/slot03_emotional_matrix/`](src/nova/slots/slot03_emotional_matrix/) | Ontology: **[§3.4]**
- **Slot 4: TRI Engine** → [`src/nova/slots/slot04_tri/`](src/nova/slots/slot04_tri/) | Ontology: **[§4.1]**
- **Slot 5: Constellation** → [`src/nova/slots/slot05_constellation/`](src/nova/slots/slot05_constellation/)
- **Slot 6: Cultural Synthesis** → [`src/nova/slots/slot06_cultural_synthesis/`](src/nova/slots/slot06_cultural_synthesis/)
- **Slot 7: Production Controls** → [`src/nova/slots/slot07_production_controls/`](src/nova/slots/slot07_production_controls/) | Flow Fabric implementation
- **Slot 8: Memory Ethics** → [`src/nova/slots/slot08_memory_ethics/`](src/nova/slots/slot08_memory_ethics/)
- **Slot 9: Distortion Protection** → [`src/nova/slots/slot09_distortion_protection/`](src/nova/slots/slot09_distortion_protection/) | Ontology: **[§8.2]**
- **Slot 10: Civilizational Deployment** → [`src/nova/slots/slot10_civilizational_deployment/`](src/nova/slots/slot10_civilizational_deployment/)

### **Understanding Core Systems**
- **Three Ledgers (Fact/Claim/Attest)** → [`src/nova/ledger/`](src/nova/ledger/) | Ontology: **[§5.2]**
- **ORP Hysteresis (5 regimes)** → [`src/nova/continuity/orp_hysteresis.py`](src/nova/continuity/orp_hysteresis.py) | Ontology: **[§4.3]**
- **Temporal Continuity** → [`src/nova/continuity/`](src/nova/continuity/) | Phase 13b implementation
- **Flow Fabric Routing** → [`src/nova/slots/slot07_production_controls/`](src/nova/slots/slot07_production_controls/) | Ontology: **[§6.2]**

### **Understanding Data Flow**
- **ORP → AVL → Ledger → Checkpoints** → [`src/nova/README.md`](src/nova/README.md) (data pipeline section)
- **Slot interaction matrix** → [`src/nova/README.md`](src/nova/README.md) (routing table)
- **Contract validation** → [`src/nova/ontology/validator.py`](src/nova/ontology/validator.py)

---

## 📁 **FILE PATTERNS FOR AI AGENTS**

### **Code Comprehension Patterns**
```
# Core system components
src/nova/slots/slot*/           # Individual slot implementations
src/nova/ledger/                # Three Ledgers system
src/nova/continuity/            # Temporal intelligence
src/nova/ontology/              # Mother Ontology v1.7.1

# Contract definitions
contracts/slot*_*.yaml          # Slot-specific contracts
contracts/*@*.yaml              # Versioned contracts

# Test organization
tests/continuity/                # ORP + AVL + temporal tests
tests/slots/                     # Slot behavior tests
tests/integration/               # Cross-slot coordination
tests/health/                    # Invariance tests

# Documentation
docs/architecture/adr/           # Architectural decisions
docs/architecture/ontology/      # Canonical specifications
docs/compliance/audits/          # Implementation audits
```

### **Search Patterns for Common Tasks**
- **Finding slot implementations**: `git grep "class.*Slot" src/nova/slots/`
- **Contract validation**: `git grep "validate_contract" src/nova/ontology/`
- **Test patterns**: `git grep "def test.*temporal" tests/continuity/`
- **Configuration**: `git grep "NOVA_WISDOM" config/`

---

## 🧠 **CODE COMPREHENSION HINTS FOR AI AGENTS**

### **Understanding Slot Architecture**
- **All slots inherit** from base slot interfaces
- **Contract validation** happens at slot initialization
- **Flow Fabric integration** via `slot07_production_controls`
- **Temporal continuity** maintained through AVL snapshots

### **Understanding Ledger System**
- **Three progressive layers**: Fact (raw) → Claim (processed) → Attest (verified)
- **Hash chaining** ensures immutability
- **Merkle trees** for Phase 14.2 checkpointing
- **ACID compliance** in PostgreSQL backend

### **Understanding Continuity Systems**
- **ORP manages 5 regime states** with hysteresis
- **AVL captures pre-transition state** immutably
- **Temporal snapshots** are deterministic and serializable
- **Regime transitions** maintain zero data loss

### **Understanding Flow Fabric**
- **Adaptive routing** with 0.1-5.0x weight modulation
- **Backpressure coordination** through Slot 7
- **Contract-based communication** with QoS guarantees
- **Real-time adaptation** to system conditions

---

## 🔗 **MAPPING TO ADRs, SPECS, CONTRACTS**

### **Architectural Decision Records**
- **ADR-012**: Semantic Mirror Integration → [`docs/architecture/adr/ADR-012-semantic-mirror-integration.md`](docs/architecture/adr/ADR-012-semantic-mirror-integration.md)
- **ADR-13**: Ledger Implementation → [`docs/architecture/adr/ADR-13-Ledger-Final.md`](docs/architecture/adr/ADR-13-Ledger-Final.md)
- **ADR-14**: Persistence Strategy → [`docs/architecture/adr/ADR-14-Ledger-Persistence.md`](docs/architecture/adr/ADR-14-Ledger-Persistence.md)
- **ADR-15**: Federation Foundation → [`docs/architecture/adr/ADR-15-Federation-Foundation.md`](docs/architecture/adr/ADR-15-Federation-Foundation.md)

### **Contract Specifications**
- **Slot Contracts**: `contracts/slot*.yaml` (10 slot contracts)
- **System Contracts**: `contracts/*.yaml` (ORP, AVL, Flow Fabric)
- **Ontology Validation**: [`src/nova/ontology/validator.py`](src/nova/ontology/validator.py)

### **Implementation Specifications**
- **Mother Ontology v1.7.1**: [`docs/architecture/ontology/_canon.yaml`](docs/architecture/ontology/_canon.yaml)
- **Phase 13b Temporal**: [`src/nova/continuity/temporal_snapshot.py`](src/nova/continuity/temporal_snapshot.py)
- **Phase 14.2 Persistence**: PostgreSQL backend (upcoming)

---

## 🚀 **QUICK START FOR AI AGENTS**

### **Immediate Orientation (5 minutes)**
1. **Read this NAVIGATION.md** completely
2. **Scan search keywords** table for your needs
3. **Follow clickable paths** to specific components
4. **Reference ontology sections** for canonical definitions
5. **Use file patterns** for systematic exploration

### **Deep Analysis Path**
1. **Start with system overview**: [`README.md`](README.md) + [`src/nova/README.md`](src/nova/README.md)
2. **Understand ontology**: [`docs/architecture/ontology/_canon.yaml`](docs/architecture/ontology/_canon.yaml)
3. **Explore slots**: [`src/nova/slots/`](src/nova/slots/) directory
4. **Understand data flow**: ORP → AVL → Ledger → Checkpoints
5. **Review contracts**: [`contracts/`](contracts/) directory

### **Modification Path**
1. **Check ontology alignment**: All changes must align with v1.7.1
2. **Update contracts**: Modify `contracts/*.yaml` first
3. **Implement code**: Follow established patterns
4. **Add tests**: Mirror structure in `tests/` directory
5. **Validate**: Run ontology validator and full test suite

---

## 📊 **REPOSITORY STRUCTURE FOR AI AGENTS**

```
nova-civilizational-architecture/
├── src/nova/                    # 🔍 START HERE for code understanding
│   ├── slots/                   # 🧠 10 cognitive slots (01-10)
│   ├── ledger/                  # 📊 Three Ledgers system
│   ├── continuity/              # ⏰ Temporal intelligence
│   ├── ontology/                # 🧬 Mother Ontology v1.7.1
│   └── README.md                # 📖 Internal technical overview
├── tests/                       # ✅ Test suite (2180 passing, 2200 collected)
│   ├── continuity/              # ORP + AVL tests
│   ├── slots/                   # Slot behavior tests
│   └── integration/             # Cross-system tests
├── docs/                        # 📚 Documentation
│   ├── architecture/            # System design & ADRs
│   ├── compliance/              # Security & audits
│   └── README.md                # 📖 Documentation index
├── contracts/                   # 📋 Contract definitions
├── config/                      # ⚙️ Configuration files
└── scripts/                     # 🔧 Maintenance utilities
```

---

## 🎯 **ZERO CONFUSION GUARANTEE**

This navigation guide ensures AI agents and contributors can:

- **Find any information instantly** using search keywords
- **Navigate complex relationships** through direct mappings
- **Understand system flow** via data pipeline explanations
- **Locate implementation details** through file patterns
- **Modify code safely** using contract and ontology references

**Result**: Zero friction forever. AI tools operate with perfect orientation.

---

*This guide is the definitive navigation reference for Nova Civilizational Architecture. Updated during Phase 14-0 Repository Consolidation.*
