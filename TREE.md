# Nova Civilizational Architecture - Phase 14 Repository Structure

**Last updated: Phase 14-0 Consolidation | Ontology v1.7.1 | 2145 Tests @ 100% Pass**

---

## 🎯 **SYSTEM ZONES OVERVIEW**

```
nova-civilizational-architecture/
├── 🔧 DEVELOPMENT CORE      # Entry points & configuration
├── 🏗️ SOURCE ARCHITECTURE   # Nova framework implementation  
├── 🧪 VALIDATION LAYER      # Testing & quality assurance
├── 📚 KNOWLEDGE BASE        # Documentation & specifications
├── ⚙️ INFRASTRUCTURE         # Operations & deployment
└── 📦 DISTRIBUTION          # Release artifacts
```

---

## 🔧 **DEVELOPMENT CORE** - Entry Points & Configuration

**Responsibilities**: Project setup, dependencies, build configuration, development workflow**

```
├── 📄 README.md              # → Project overview & getting started
├── 📄 requirements.txt       # → Python dependencies (core runtime)
├── 📄 Makefile               # → Build automation & common tasks
├── 🐍 app.py                 # → 🚀 MAIN APPLICATION ENTRYPOINT
├── 🐍 auth.py                # → Authentication & authorization
├── 🐍 conftest.py            # → Global test configuration
├── 🐍 logging_config.py      # → Centralized logging setup
├── 🐍 slot_loader.py         # → Dynamic slot loading system
├── 🐍 src_bootstrap.py       # → Source code bootstrapping
├── 🐍 content_analysis.py    # → Content processing utilities
├── 🐍 lifespan.py            # → ASGI lifespan management
├── 🐍 verify_pilot_ready.py  # → System readiness validation
├── 📄 .gitignore             # → Git ignore patterns
├── 📄 .gitattributes         # → Git file attributes
├── 📁 config/                # → ⚙️ Configuration files (13 files)
│   ├── 📄 pyproject.toml     # → Python project metadata & dependencies
│   ├── 📄 pytest.ini          # → Test framework configuration
│   ├── 📄 mypy.ini            # → Type checking rules
│   ├── 📄 .env.example        # → Environment variables template
│   └── 📄 feature_flags.py    # → Feature flag definitions
├── 📁 .github/               # → CI/CD workflows & security
│   └── 📄 .secrets.baseline   # → Secret scanning configuration
└── 📁 .build/                # → Build artifacts (reserved for future)
```

**AI Agent Search Heuristics**:
- `app.py` = Application entry point
- `config/` = All configuration files
- `requirements.txt` = Runtime dependencies

---

## 🏗️ **SOURCE ARCHITECTURE** - Nova Framework Implementation

**Responsibilities**: Core Nova system, 10-slot cognition, temporal continuity, truth verification**

```
├── 📁 src/nova/               # → 🏗️ NOVA FRAMEWORK CORE
│   ├── 📖 README.md           # → 📚 Internal architecture overview
│   ├── 📁 slots/              # → 🧠 10 COGNITIVE SLOTS (01-10)
│   │   ├── 📁 slot01_truth_anchor/        # → Reality verification
│   │   ├── 📁 slot02_deltathresh/         # → Pattern detection  
│   │   ├── 📁 slot03_emotional_matrix/    # → Cognitive processing
│   │   ├── 📁 slot04_tri/                 # → Flow-mesh reasoning
│   │   ├── 📁 slot05_constellation/       # → Spatial navigation
│   │   ├── 📁 slot06_cultural_synthesis/  # → Ethical guardrails
│   │   ├── 📁 slot07_production_controls/ # → Circuit breaker system
│   │   ├── 📁 slot08_memory_ethics/       # → ACL protection
│   │   ├── 📁 slot09_distortion_protection/ # → Hybrid defense
│   │   └── 📁 slot10_civilizational_deployment/ # → MetaLegitimacySeal
│   ├── 📁 ledger/             # → 📊 THREE LEDGERS SYSTEM
│   │   ├── 🐍 factory.py      # → 🚀 LEDGER CREATION ENTRYPOINT
│   │   └── 📁 [fact|claim|attest]_ledger/ # → Ledger implementations
│   ├── 📁 continuity/         # → ⏰ TEMPORAL CONTINUITY SYSTEMS
│   │   ├── 🐍 orp_hysteresis.py    # → 🚀 REGIME MANAGEMENT ENTRYPOINT
│   │   ├── 🐍 temporal_snapshot.py # → Phase 13b temporal capture
│   │   └── 🐍 avalon_ledger.py     # → Autonomous verification
│   └── 📁 ontology/           # → 🧬 MOTHER ONTOLOGY v1.7.1
│       ├── 🐍 loader.py       # → 🚀 ONTOLOGY LOADING ENTRYPOINT
│       └── 📁 specs/          # → Ontology specifications
```

**AI Agent Search Heuristics**:
- `src/nova/` = All core implementation
- `slots/slot*/` = Individual cognitive components
- `continuity/` = Temporal intelligence systems
- `ledger/` = Truth verification systems
- `ontology/` = Foundational specifications

---

## 🧪 **VALIDATION LAYER** - Testing & Quality Assurance

**Responsibilities**: Comprehensive testing, quality validation, system verification**

```
├── 📁 tests/                  # → 🧪 TEST SUITE (2145 tests @ 100%)
│   ├── 📖 README.md           # → Test suite documentation
│   ├── 🐍 conftest.py         # → Global test fixtures
│   ├── 📁 continuity/         # → ORP + AVL + temporal tests
│   ├── 📁 slots/              # → Slot-specific behavior tests
│   ├── 📁 integration/        # → Cross-slot coordination tests
│   ├── 📁 health/             # → System stability tests
│   ├── 📁 api/                # → API endpoint tests
│   ├── 📁 attestation/        # → Cryptographic verification tests
│   ├── 📁 concurrency/        # → Thread safety tests
│   ├── 📁 chaos/              # → Fault injection tests
│   ├── 📁 federation/         # → Multi-peer coordination tests
│   ├── 📁 performance/        # → Benchmark tests
│   ├── 📁 slo/                # → Service level objective tests
│   └── 📁 meta/               # → Documentation validation tests
```

**AI Agent Search Heuristics**:
- `tests/continuity/` = Temporal system tests
- `tests/slots/` = Component behavior tests
- `tests/integration/` = System interaction tests

---

## 📚 **KNOWLEDGE BASE** - Documentation & Specifications

**Responsibilities**: Complete documentation, specifications, guides, and historical records**

```
├── 📁 docs/                   # → 📚 COMPREHENSIVE DOCUMENTATION
│   ├── 📖 README.md           # → Documentation index & navigation
│   ├── 📖 NAVIGATION.md       # → AI agent navigation guide
│   ├── 📖 GLOSSARY.md         # → Unified technical vocabulary
│   ├── 📖 ARCHITECTURE.md     # → System architecture overview
│   ├── 📁 architecture/       # → 🏗️ ARCHITECTURE & DESIGN
│   │   ├── 📁 ontology/       # → Mother Ontology v1.7.1 specs
│   │   ├── 📁 adr/            # → Architectural decision records
│   │   └── 📄 system_map.yaml # → Component relationships
│   ├── 📁 guides/             # → 📖 USER GUIDES
│   │   ├── 📁 quickstart/     # → Getting started guides
│   │   └── 📁 contributing/   # → Contribution guidelines
│   ├── 📁 api/                # → 🔌 API DOCUMENTATION
│   │   ├── 📁 contracts/      # → Contract specifications
│   │   └── 📁 slots/          # → Slot API documentation
│   ├── 📁 operations/         # → ⚙️ OPERATIONS & MONITORING
│   │   ├── 📁 runbooks/       # → Operational procedures
│   │   ├── 📁 alerts/         # → Alert configurations
│   │   └── 📁 monitoring/     # → Monitoring setup guides
│   ├── 📁 compliance/         # → 🔒 SECURITY & COMPLIANCE
│   │   ├── 📁 security/       # → Security policies
│   │   ├── 📁 audits/         # → Audit reports & assessments
│   │   ├── 📁 defects/        # → Defect tracking
│   │   └── 📁 attestations/   # → System attestations
│   ├── 📁 research/           # → 🔬 RESEARCH & ANALYSIS
│   │   ├── 📁 papers/         # → Research publications
│   │   ├── 📁 analysis/       # → Analysis reports
│   │   └── 📁 manifests/      # → Epoch manifests
│   └── 📁 archive/            # → 🗂️ HISTORICAL DOCUMENTATION
│       ├── 📁 phase-docs/     # → Phase-specific documentation
│       └── 📁 legacy/         # → Legacy system documentation
├── 📁 contracts/              # → 📋 SYSTEM CONTRACTS & SPECS
│   ├── 📄 slot*_*.yaml        # → Slot-specific contracts
│   ├── 📄 *ledger*@*.yaml     # → Ledger contracts
│   ├── 📄 orp@*.yaml          # → Regime policy contracts
│   └── 📁 validators/         # → Contract validation logic
```

**AI Agent Search Heuristics**:
- `docs/README.md` = Documentation index
- `docs/NAVIGATION.md` = Navigation guide
- `docs/GLOSSARY.md` = Technical vocabulary
- `docs/architecture/` = System design
- `contracts/` = All specifications

---

## ⚙️ **INFRASTRUCTURE** - Operations & Deployment

**Responsibilities**: System operations, monitoring, deployment, and maintenance**

```
├── 📁 scripts/                # → 🔧 UTILITIES & MAINTENANCE
│   ├── 📖 README.md           # → Script documentation
│   ├── 🐍 validate_ontology_structure.py # → Ontology validation
│   ├── 📁 maintenance/        # → Maintenance scripts
│   │   └── 🐍 sunlight_scan.py # → Documentation governance
│   └── 🐍 setup_bookmarks.py  # → Development environment setup
├── 📁 ops/                    # → 📊 OPERATIONS & MONITORING
│   ├── 📖 README.md           # → Operations guide
│   └── 📁 alerts/             # → Alert configurations
│       └── 📄 nova-phase2.rules.yml # → Prometheus alert rules
├── 📁 monitoring/             # → 📈 MONITORING INFRASTRUCTURE
│   ├── 📄 docker-compose.yml  # → Monitoring stack deployment
│   ├── 📁 grafana/            # → Dashboard configurations
│   ├── 📁 prometheus/         # → Metrics collection setup
│   └── 🐍 standalone-prometheus.py # → Standalone monitoring
├── 📁 agents/                 # → 🤖 AI COLLABORATION FRAMEWORK
│   └── 📖 nova_ai_operating_framework.md # → AI operating principles
└── 📁 archive/                # → 🗂️ LEGACY MIGRATION ARTIFACTS
    ├── 📁 legacy-slot-migration/ # → Pre-namespaced documentation
    └── 📖 README.md           # → Archive documentation
```

**AI Agent Search Heuristics**:
- `scripts/` = Utility and maintenance tools
- `ops/` = Operational procedures
- `monitoring/` = Observability setup
- `agents/` = AI collaboration guidelines

---

## 📦 **DISTRIBUTION** - Release Artifacts

**Responsibilities**: Release packages, academic publishing, reproducibility**

```
├── 📦 nova_civilizational_architecture_v9.0-final.tar.gz
├── 📦 nova_reproducibility_kit.zip
├── 📦 phase11_docs_archive.tar.gz
└── 📄 CITATION.cff            # → Academic citation metadata
```

---

## 🎯 **AI AGENT QUICK REFERENCE**

### **Finding Code Entry Points**
- **Main Application**: `app.py`
- **Ledger System**: `src/nova/ledger/factory.py`
- **Regime Management**: `src/nova/continuity/orp_hysteresis.py`
- **Ontology Loading**: `src/nova/ontology/loader.py`

### **Finding Documentation**
- **Architecture Overview**: `docs/README.md`
- **Navigation Guide**: `docs/NAVIGATION.md`
- **Technical Vocabulary**: `docs/GLOSSARY.md`
- **Internal Details**: `src/nova/README.md`

### **Finding Specifications**
- **System Contracts**: `contracts/`
- **Ontology Specs**: `docs/architecture/ontology/`
- **Test Suite**: `tests/`

### **Finding Operations**
- **Monitoring Setup**: `monitoring/`
- **Alert Configuration**: `ops/alerts/`
- **Maintenance Scripts**: `scripts/`

---

## 📊 **REPOSITORY METRICS**

- **Total Files**: ~2,500+ files
- **Test Coverage**: 2145 tests @ 100% pass rate
- **Ontology Version**: Mother Ontology v1.7.1
- **Phase Status**: Phase 14-0 (Consolidated) → Phase 14.2 (PostgreSQL Persistence)
- **Documentation Integrity**: Sunlight Doctrine compliant

---

*This repository structure reflects Phase 14-0 consolidation and provides a clean, navigable foundation for continued development. All directories are organized by system zones with clear responsibilities and AI agent search heuristics.*
