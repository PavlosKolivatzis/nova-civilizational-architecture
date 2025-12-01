# Nova Civilizational Architecture - Directory Tree

```
nova-civilizational-architecture/
├── 📁 config/           # Configuration files (moved from root)
│   ├── .env.example     # Environment variables template
│   ├── pyproject.toml   # Python project configuration
│   ├── pytest.ini       # Test configuration
│   ├── mypy.ini         # Type checking configuration
│   ├── .editorconfig    # Code style settings
│   ├── .pre-commit-config.yaml  # Pre-commit hooks
│   ├── commitlint.config.js    # Commit message linting
│   ├── package.json     # NPM dependencies
│   ├── vercel.json      # Vercel deployment config
│   ├── zenodo-metadata.json    # Academic publishing metadata
│   ├── meta.yaml        # Feature flags and metadata
│   ├── feature_flags.py # Feature flag definitions
│   ├── adaptive_links.yaml     # Link configuration
│   ├── peers.yaml       # Federation peer configuration
│   └── .coveragerc      # Coverage configuration
├── 📁 .github/          # CI/CD workflows (moved from root)
│   └── .secrets.baseline  # Secret scanning baseline
├── 📁 .build/           # Build artifacts (empty - for future use)
├── 📁 src/nova/         # 🏗️ Core framework code
│   ├── slots/           # 10 cognitive processing slots
│   │   ├── slot01_truth_anchor/     # Reality verification
│   │   ├── slot02_deltathresh/      # Pattern detection
│   │   ├── slot03_emotional_matrix/ # Cognitive processing
│   │   ├── slot04_tri/              # Flow-mesh reasoning
│   │   ├── slot05_constellation/    # Spatial navigation
│   │   ├── slot06_cultural_synthesis/ # Ethical guardrails
│   │   ├── slot07_production_controls/ # Circuit breaker
│   │   ├── slot08_memory_guard/     # ACL & self-healing
│   │   ├── slot09_distortion_protection/ # Hybrid defense
│   │   └── slot10_civilizational_deployment/ # MetaLegitimacySeal
│   ├── ledger/          # Three Ledgers system
│   │   ├── factory.py   # Ledger creation
│   │   └── [fact|claim|attest]_ledger/ # Ledger implementations
│   ├── ontology/        # Mother Ontology v1.7.1
│   │   ├── loader.py    # Ontology loading
│   │   └── specs/       # Ontology specifications
│   ├── continuity/      # Temporal continuity systems
│   │   └── orp_hysteresis.py # Operational Regime Policy
│   └── README.md        # Framework overview
├── 📁 tests/            # 🧪 Test suite (2,089 tests)
│   ├── api/             # API endpoint tests
│   ├── attestation/     # Cryptographic verification
│   ├── chaos/           # Resilience testing
│   ├── concurrency/     # Thread safety tests
│   ├── continuity/      # Temporal system tests
│   ├── federation/      # Multi-peer coordination
│   ├── health/          # Health check tests
│   ├── orchestrator/    # Coordination layer tests
│   ├── performance/     # Performance benchmarks
│   ├── property/        # Property-based testing
│   ├── slo/             # Service level objectives
│   ├── meta/            # Documentation validation
│   ├── slot*/           # Slot-specific tests
│   ├── conftest.py      # Global test fixtures
│   └── README.md        # Test suite documentation
├── 📁 docs/             # 📖 Documentation (comprehensive)
│   ├── README.md        # Documentation index
│   ├── NAVIGATION.md    # Navigation guide
│   ├── GLOSSARY.md      # Terms and concepts
│   ├── ARCHITECTURE.md  # System architecture
│   ├── SYSTEM_ANALYSIS.md # System analysis
│   ├── architecture/    # Architecture documentation
│   │   ├── ontology/    # Ontology specifications
│   │   ├── adr/         # Architectural decisions
│   │   └── system_map.yaml # Component relationships
│   ├── guides/          # User guides
│   │   ├── quickstart/  # Getting started
│   │   └── contributing/ # Contribution guidelines
│   ├── api/             # API documentation
│   │   ├── contracts/   # Contract specifications
│   │   └── slots/       # Slot API docs
│   ├── operations/      # Operations & monitoring
│   │   ├── runbooks/    # Operational procedures
│   │   ├── alerts/      # Alert configurations
│   │   └── monitoring/  # Monitoring setup
│   ├── compliance/      # Security & compliance
│   │   ├── security/    # Security policies
│   │   ├── audits/      # Audit reports
│   │   ├── defects/     # Defect tracking
│   │   └── attestations/ # System attestations
│   ├── research/        # Research & analysis
│   │   ├── papers/      # Research papers
│   │   ├── analysis/    # Analysis reports
│   │   └── manifests/   # Epoch manifests
│   └── archive/         # Historical documentation
│       ├── phase-docs/  # Phase-specific docs
│       └── legacy/      # Legacy system docs
├── 📁 contracts/        # 📋 System contracts
│   ├── autonomous_verification_ledger@1.yaml
│   ├── csi@1.yaml       # Cognitive State Interface
│   ├── csi_breakdown@1.yaml
│   ├── distortion_detection_response.schema.json
│   ├── feature.ids.contract.json
│   ├── hysteresis_decision@1.yaml
│   ├── memory_resonance_stats@1.yaml
│   ├── meta_lens_report@1.json
│   ├── mse@1.yaml       # Meta Stability Engine
│   ├── orp@1.yaml       # Operational Regime Policy
│   ├── orp_stabilization@1.yaml
│   ├── predictive_consistency@1.yaml
│   ├── predictive_consistency_gap@1.yaml
│   ├── predictive_pattern_alert@1.yaml
│   ├── predictive_snapshot@1.yaml
│   ├── rc_attestation@1.yaml
│   ├── rc_criteria_result@1.yaml
│   ├── regime@1.yaml
│   ├── regime_transition_ledger@1.yaml
│   ├── slot_map.json    # Slot maturity mapping
│   ├── slot*_*.yaml     # Slot-specific contracts
│   ├── temporal_consistency@1.yaml
│   ├── transformation_geometry@1.yaml
│   ├── tri_truth_signal@1.yaml
│   ├── urf@1.yaml       # Universal Reference Framework
│   └── validators/      # Contract validators
├── 📁 scripts/          # 🔧 Utilities & maintenance
│   ├── bootstrap_dev_env.sh     # Development setup
│   ├── validate_ontology_structure.py # Ontology validation
│   ├── maintenance/     # Maintenance scripts
│   │   └── sunlight_scan.py    # Documentation governance
│   └── README.md        # Script documentation
├── 📁 ops/              # 📊 Operations & monitoring
│   ├── alerts/          # Alert configurations
│   │   └── nova-phase2.rules.yml # Prometheus alerts
│   └── README.md        # Operations guide
├── 📁 monitoring/       # 📈 Monitoring setup
│   ├── docker-compose.yml      # Monitoring stack
│   ├── grafana/         # Dashboard configurations
│   ├── prometheus/      # Metrics collection
│   └── standalone-prometheus.py # Standalone monitoring
├── 📁 agents/           # 🤖 AI collaboration framework
│   └── nova_ai_operating_framework.md # Operating principles
├── 📁 archive/          # 🗂️ Legacy migration artifacts
│   ├── legacy-slot-migration/  # Pre-namespaced docs
│   └── README.md        # Archive documentation
├── 🔧 Root Files (14 essential files)
│   ├── README.md        # Project overview
│   ├── requirements.txt # Python dependencies
│   ├── Makefile         # Build automation
│   ├── app.py           # Main application
│   ├── auth.py          # Authentication
│   ├── conftest.py      # Global test config
│   ├── logging_config.py # Logging setup
│   ├── slot_loader.py   # Slot loading utilities
│   ├── src_bootstrap.py # Source bootstrapping
│   ├── content_analysis.py # Content analysis
│   ├── lifespan.py      # ASGI lifespan management
│   ├── verify_pilot_ready.py # Pilot readiness checks
│   ├── .gitignore       # Git ignore patterns
│   └── .gitattributes   # Git attributes
└── 📦 Distribution Files
    ├── nova_civilizational_architecture_v9.0-final.tar.gz
    ├── nova_reproducibility_kit.zip
    ├── phase11_docs_archive.tar.gz
    └── CITATION.cff     # Citation metadata
```

## Legend

- 📁 **Directory** - Organizational folder
- 📖 **Documentation** - Markdown/text files
- 🏗️ **Source Code** - Python implementation
- 🧪 **Tests** - Test files and fixtures
- 📋 **Contracts** - System specifications
- 🔧 **Tools** - Scripts and utilities
- 📊 **Operations** - Monitoring and alerts
- 🤖 **AI Framework** - Collaboration guidelines
- 🗂️ **Archive** - Historical content
- 🔧 **Root Files** - Essential repository files
- 📦 **Distribution** - Release artifacts

## Navigation Tips

- **New to the project?** Start with `docs/NAVIGATION.md`
- **Understanding architecture?** See `docs/architecture/`
- **Running tests?** Check `tests/README.md`
- **Contributing?** Read `docs/guides/contributing/`
- **API documentation?** Look in `docs/api/`

---

*Generated during Phase 14-0 Repository Consolidation - Last updated: 2025-12-01*