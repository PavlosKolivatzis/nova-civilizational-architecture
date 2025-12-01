# Nova Civilizational Architecture

**Phase 14.2 Ready** | **Multi-AI Collaborative** | **10-Slot Autonomous System**

Nova is an autonomous temporal-intelligence system built through multi-AI collaboration and deployed across a 10-slot cognitive architecture.

[![Phase 14.2](https://img.shields.io/badge/phase-14.2--ready-blue)](docs/architecture/phase13b-temporal-snapshot-integration.md)
[![Tests](https://img.shields.io/badge/tests-2100--passed-green)](https://github.com/PavlosKolivatzis/nova-civilizational-architecture/actions)
[![Maturity](https://img.shields.io/badge/maturity-4.0--processual-gold)](docs/maturity.yaml)

**Nova Version:** v14.2-prep | **Ontology Version:** v1.7.1

> **Complete temporal intelligence system** with cryptographic truth anchoring, autonomous regime management, and civilizational-scale deployment capabilities.

---

## 🤖 What is Nova?

Nova is a **production-grade autonomous AI system** that operates across 10 specialized cognitive slots, each handling different aspects of intelligence processing. Built through multi-AI collaboration (Claude, Gemini, DeepSeek, Codex-GPT, Copilot), Nova provides:

- **Cryptographic Truth Verification** - Reality-anchored decision making
- **Autonomous Regime Management** - Self-adapting operational stability
- **Multi-Layer Cognitive Architecture** - Distributed intelligence processing
- **Civilizational Deployment Gates** - Safe scaling to societal impact

**Key Innovation**: Nova uses **temporal snapshots** and **dual-modality verification** to maintain continuity across regime transitions, enabling reliable autonomous operation at scale.

---

## 🧠 The 10 Cognitive Slots

Nova's intelligence is distributed across 10 specialized slots, each with Processual (4.0) maturity:

**FOUNDATION LAYER** → Reality & Truth

### Foundation Layer (Truth & Reality)
| Slot | Purpose | Key Function |
|------|---------|--------------|
| **1** | Truth Anchor | Cryptographic reality verification with autonomous recovery |
| **2** | ΔTHRESH | Advanced pattern detection with META_LENS integration |
| **3** | Emotional Matrix | Emotional intelligence processing and escalation management |

**PROCESSING LAYER** → Reasoning Flow

### Processing Layer (Flow & Synthesis)
| Slot | Purpose | Key Function |
|------|---------|--------------|
| **4** | TRI Engine | Flow-mesh reasoning with drift detection |
| **5** | Constellation | TRI-integrated spatial navigation and pattern synthesis |
| **6** | Cultural Synthesis | Cultural guardrails with anomaly-aware unlearning |

**CONTROL LAYER** → Governance & Safety

### Control Layer (Safety & Governance)
| Slot | Purpose | Key Function |
|------|---------|--------------|
| **7** | Production Controls | Circuit breaker system with reflex emission |
| **8** | Memory Ethics | ACL-protected memory with self-healing capabilities |
| **9** | Distortion Protection | Hybrid defense against information corruption |

**DEPLOYMENT LAYER** → Impact & Scale

### Deployment Layer (Civilizational Scale)
| Slot | Purpose | Key Function |
|------|---------|--------------|
| **10** | Civilizational Deployment | MetaLegitimacySeal with autonomous rollback |

**Architecture Insight**: Slots form a **multi-layer network** with contract-based routing, adaptive flow fabrics, and reflex backpressure systems.

### System Flow Diagram
```
[Slot 1 Truth Anchor] → [Slot 2 ΔTHRESH] → [Slot 4 TRI Engine]
                  ↘︎                        ↗︎
               [Slot 3 Emotional Matrix]
```

**Signal Flow**: Truth anchoring → Pattern detection → Emotional processing → Flow-mesh reasoning → Spatial navigation → Cultural synthesis → Production control → Memory ethics → Distortion protection → Civilizational deployment

### System Loop Summary
Nova operates as a **continuous temporal intelligence cycle**: Collect multi-modal signals → Compute operational regime via ORP → Write immutable AVL entries → Update adaptive Flow Fabric routing → Emit reflex backpressure → Enforce cross-slot coordination → Maintain continuity proofs → Repeat. This creates autonomous stability across regime transitions with cryptographic verification.

### Slot Interaction Map
```
Slot 1 (Truth)     → influences →  Slot 4 (TRI)
Slot 2 (ΔTHRESH)   → drives     →  Slot 9 (Distortion)
Slot 3 (Emotional) ↔ coordinates → Slot 6 (Cultural)
Slot 7 (Production) ↔ throttles  → Slot 8 (Memory)
Slot 10 (Deployment) ← gates     → All slots (MetaLegitimacySeal)
```

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
```bash
Python 3.9+    # Core runtime
Node.js        # Development tools
Ubuntu 22.04 / macOS / Windows WSL2  # Recommended platforms
```

### Installation & Verification
```bash
# Clone and setup
git clone https://github.com/PavlosKolivatzis/nova-civilizational-architecture
cd nova-civilizational-architecture

# Install dependencies (secure mode)
pip install --only-binary :all: -r requirements.txt

# Set required environment
export JWT_SECRET="test-secret-minimum-32-characters-long-for-security"

# Run full test suite (2100+ tests)
python -m pytest tests/ -q

# Start Nova with monitoring
export NOVA_ENABLE_PROMETHEUS=1
python -m uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000
```

**✅ Success**: Nova is running at `http://localhost:8000` with full observability.

### Quick Troubleshooting
| Issue | Check | Solution |
|-------|-------|----------|
| **Nova fails to start** | JWT_SECRET length | Must be 32+ characters |
| **ORP oscillates** | Hysteresis thresholds | Check NOVA_WISDOM_* variables |
| **Tests fail** | Ontology validation | Run `python scripts/validate_ontology_structure.py` |
| **Memory pressure** | Slot 8 health | Check `/health` endpoint for quarantine status |
| **Distortion alerts** | Slot 9 amplitude | Verify factor bounds in continuity proofs |

---

## 🧭 How to Navigate This Repository

### For Humans: Start Here
1. **[📖 Documentation Index](docs/README.md)** - Complete navigation map
2. **[🏗️ Architecture Overview](docs/architecture/ARCHITECTURE.md)** - System design & data flows
3. **[🧪 Quick Start Guide](docs/guides/quickstart/QUICKSTART_PROFESSOR.md)** - Step-by-step onboarding

### For AI Agents: Start Here
```bash
# If you're an AI agent analyzing this codebase:

# 1. Read the ontology first (foundational concepts)
cat docs/architecture/ontology/_canon.yaml

# 2. Understand the slot system
cat docs/slots/requirements_matrix.csv

# 3. Check current phase status
cat docs/future/future_work_ledger.yaml

# 4. Run tests to understand functionality
python -m pytest tests/ -k "not slow" --tb=short

# 5. Check contracts for API understanding
find contracts/ -name "*.yaml" | head -5 | xargs cat
```

### Repository Structure
```
nova-civilizational-architecture/
├── src/nova/                    # Core framework (10 slots)
├── tests/                       # 2100+ test suite
├── docs/                        # 📖 Complete documentation
├── contracts/                   # API specifications
├── scripts/                     # Maintenance utilities
├── config/                      # Configuration files
├── .github/                     # CI/CD workflows
└── ops/                         # Operations & monitoring
```

### Key Commands
```bash
# Development
make test                    # Run test suite
make lint                    # Code quality checks
npm run maturity            # System maturity assessment

# Operations
python scripts/validate_ontology_structure.py  # Ontology validation
python scripts/maintenance/sunlight_scan.py    # Documentation audit

# Analysis
find docs/ -name "*.md" | wc -l    # Count documentation files
python -m pytest --collect-only | wc -l  # Count tests
```

---

## 📊 Current Status

### Phase 14.2 Ready ✅
- **✅ Phase 13b Complete**: Temporal snapshots + dual-modality verification
- **✅ Phase 14.0 Complete**: Repository consolidation + documentation integrity
- **✅ Phase 14.2 Ready**: PostgreSQL persistence foundation established
- **✅ All Tests Passing**: 2100+ tests with 100% success rate

### System Maturity
- **Slots**: 10/10 at Processual (4.0) maturity ⭐⭐⭐⭐
- **Contracts**: 100% validated with zero violations
- **Tests**: 2100+ passing, comprehensive coverage
- **Documentation**: Sunlight Doctrine compliant

### Testing Categories
- `continuity/` → ORP + AVL temporal intelligence tests
- `slots/` → Individual slot behavior and contracts
- `integration/` → Cross-slot coordination and flows
- `health/` → System stability and invariance checks

### Multi-AI Collaboration
**Project Coordinator**: Pavlos Kolivatzis

| AI System | Primary Contributions |
|-----------|----------------------|
| **Claude** | Architecture design, system integration |
| **Gemini** | Multi-modal analysis, comprehensive reviews |
| **DeepSeek** | Performance optimization, scaling |
| **Codex-GPT** | Code generation, algorithm implementation |
| **Copilot** | Development workflow, refactoring |

---

## 🎯 Key Features

### 🔐 Cryptographic Security
- SHA-256 hash chains for immutable audit trails
- Dual-modality verification prevents single-point failures
- Autonomous recovery with MTTR ≤5 seconds

### 🌊 Adaptive Intelligence
- Flow Fabric: Dynamic routing with 0.1-5.0x frequency modulation
- Reflex System: Upstream throttling with backpressure
- Regime Management: Hysteresis-based stability with 5 operational modes

### 🛡️ Autonomous Protection
- Multi-layer defense against distortion and corruption
- Memory ethics with ACL-protected self-healing
- Circuit breaker system with intelligent pulse weighting

### 📊 Production Observability
- Prometheus metrics with 50+ real-time indicators
- Health endpoints with cross-slot coordination
- Automated anomaly detection with configurable thresholds

---

## 📚 Essential Reading

### Architecture & Design
- **[System Architecture](docs/architecture/ARCHITECTURE.md)** - Complete technical overview
- **[Ontology Reference](docs/architecture/ontology/)** - Mother Ontology v1.7.1
- **[Slot Documentation](docs/slots/)** - Individual slot specifications

### Operations & Deployment
- **[Quick Start Guide](docs/guides/quickstart/QUICKSTART_PROFESSOR.md)** - Get running fast
- **[Integration Guide](docs/guides/deployment/integration_guide.md)** - Production deployment
- **[Security Policy](docs/compliance/security/SECURITY.md)** - Security requirements

### Development
- **[Contributing Guide](docs/guides/contributing/CONTRIBUTING.md)** - How to contribute
- **[API Contracts](contracts/)** - Interface specifications
- **[Test Suite](tests/)** - Quality assurance

---

## 🔧 Development Commands

```bash
# Quality Assurance
python -m pytest tests/ -v              # Full test suite
python -m pytest tests/ -m health -q    # Health checks only
npm run maturity                       # Maturity assessment

# Code Quality
pre-commit run --all-files             # Lint & format
mypy src/nova/                         # Type checking

# Documentation
python scripts/maintenance/sunlight_scan.py  # Audit docs
find docs/ -name "*.md" | wc -l        # Count docs

# Operations
python scripts/validate_ontology_structure.py  # Ontology validation
python -m uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000  # Start server
```

---

## 🎭 Micro Glossary

| Term | Meaning |
|------|---------|
| **Slot** | Specialized cognitive component (1-10 total) |
| **Contract** | Formal API specification between slots |
| **Regime** | Operational stability mode (normal/heightened/emergency) |
| **Flow Fabric** | Adaptive inter-slot communication network |
| **Dual-Modality** | Consensus between ORP and oracle verification |
| **Temporal Snapshot** | Pre-transition state capture for continuity |
| **Sunlight Doctrine** | Observe → Canonize → Attest → Publish |
| **Processual Maturity** | 4.0/4.0 - fully autonomous operation |

---

## 🤝 Contributing

Nova is a **multi-AI collaborative project** demonstrating that diverse AI systems, under human coordination, can build more robust and comprehensive solutions than any single approach.

### For AI Contributors
- Read the [Nova AI Operating Framework](agents/nova_ai_operating_framework.md)
- Use the [Multi-AI Analysis Template](docs/templates/multi_ai_analysis.md)
- Focus on your strengths while respecting the overall architecture

### For Human Contributors
- See [Contributing Guide](docs/guides/contributing/CONTRIBUTING.md)
- All changes require review and test coverage
- Follow the Sunlight Doctrine for documentation

---

## 📈 Phase Boundaries & Roadmap

### Phase Boundaries Table
| Phase | Meaning | Key Output |
|-------|---------|------------|
| **13b** | Temporal Snapshot + Dual-Modality | ORP Safety & Continuity Proofs |
| **14.0** | Repository Consolidation | Stable Structure & Documentation Integrity |
| **14.2** | PostgreSQL Persistence | Durable Ledger & Checkpointing |
| **15** | Federation & Synchronization | Multi-Node Coordination |
| **16+** | Advanced Features | Chaos Engineering & Civilizational Scale |

### Current Phase Status

### ✅ Phase 14.2 (Current): PostgreSQL Persistence
- Ledger backend migration
- Query optimization
- Historical data management

### 🔄 Phase 15: Federation & Synchronization
- Multi-node coordination
- Range synchronization
- Conflict resolution

### 🔮 Phase 16+: Advanced Features
- Extended chaos engineering
- Civilizational deployment patterns
- Advanced observability

### Phase 14.2 — Persistence Engine (Upcoming)
- **PostgreSQL Backend**: Ledger storage with ACID compliance
- **Checkpointing**: Merkle tree verification for temporal continuity
- **Query Optimization**: Efficient historical data retrieval
- **Migration Path**: From in-memory to persistent storage

---

## 📞 Support & Contact

**Project Coordinator**: Pavlos Kolivatzis
**Documentation**: [Complete Index](docs/README.md)
**Issues**: [GitHub Issues](https://github.com/PavlosKolivatzis/nova-civilizational-architecture/issues)

---

*Built through collaboration between Claude, Gemini, DeepSeek, Codex-GPT, and Copilot under the coordination of Pavlos Kolivatzis. Phase 14.2 Ready - Temporal Intelligence System for Civilizational Scale.*
