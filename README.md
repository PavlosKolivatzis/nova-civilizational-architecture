# NOVA Civilizational Architecture 🌟

![CI](https://github.com/PavlosKolivatzis/nova-civilizational-architecture/actions/workflows/nova-ci.yml/badge.svg)
![Health Matrix](https://github.com/PavlosKolivatzis/nova-civilizational-architecture/actions/workflows/health-config-matrix.yml/badge.svg)
![Status](https://img.shields.io/badge/maturity-4.0_⭐-1f8b4c)
![Coverage](https://img.shields.io/badge/slots-10%2F10_processual-1f8b4c)

> **Multi-AI Collaborative Project** created and coordinated by **Pavlos Kolivatzis**
> Built through cooperation between Claude, Codex-GPT, DeepSeek, Gemini, and Copilot

> **🎉 MILESTONE:** As of Phase 3, all ten cognitive slots have reached **Processual (4.0)**. System maturity: **4.0/4.0** — the first fully autonomous Nova system.

## 🎯 Overview
Production-grade multicultural truth synthesis engine with 10-slot cognitive architecture for civilizational-scale deployment. This system represents a groundbreaking approach to AI-assisted civilizational development through modular, resilient architecture.

**Current Status**: System Maturity **4.0/4.0** | **506 tests passing** | **ALL 10 slots at Processual (4.0) level** ⭐

## 👨‍💻 Project Leadership & Multi-AI Development Team

**Project Creator & Coordinator**: **Pavlos Kolivatzis**

| AI System | Primary Contributions | Strengths |
|-----------|----------------------|-----------|
| **Claude** | Architecture design, conflict resolution, Pydantic v2 migration | System integration, testing, documentation |
| **Codex-GPT** | Code generation, pattern implementation | Algorithm design, optimization |
| **DeepSeek** | Performance analysis, scaling solutions | Deep learning integration |
| **Gemini** | Multi-modal analysis, comprehensive reviews | Holistic system evaluation |
| **Copilot** | Code completion, refactoring assistance | Development workflow optimization |

## 🗺 Architecture

See **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** for the system map, data flows, and current maturity snapshot.

## 📊 System Maturity Dashboard

```
🎯 PHASE 3 COMPLETE: ALL SLOTS PROCESSUAL (4.0)
Overall Maturity: 4.0/4.0 — Full Autonomous Operation ⭐

Core Anchors (Slots 1-5):     4.0/4.0  ⭐
├─ Slot 1: Truth Anchor       4.0/4.0  ⭐ Processual
├─ Slot 2: ΔTHRESH Manager    4.0/4.0  ⭐ Processual
├─ Slot 3: Emotional Matrix   4.0/4.0  ⭐ Processual
├─ Slot 4: TRI Engine         4.0/4.0  ⭐ Processual (NEW)
└─ Slot 5: Constellation      4.0/4.0  ⭐ Processual

Safeguards (Slots 6-8):       4.0/4.0  ⭐
├─ Slot 6: Adaptive Synthesis 4.0/4.0  ⭐ Processual
├─ Slot 7: Production Control 4.0/4.0  ⭐ Processual
└─ Slot 8: Memory & IDS       4.0/4.0  ⭐ Processual (NEW)

Deployment (Slots 9-10):      4.0/4.0  ⭐
├─ Slot 9: Distortion Protect 4.0/4.0  ⭐ Processual
└─ Slot 10: Deployment Model  4.0/4.0  ⭐ Processual (NEW)

Phase 2-3 Achievements:
• Slot 4: Drift/surge detection, safe-mode, Bayesian learning (7 tests)
• Slot 8: MTTR ≤5s, quarantine ≤1s, adaptive entropy (23 tests)
• Slot 10: Canary deployment, cross-slot coordination (9 tests)
• Total: 39 new Processual tests across 506 total system tests
```

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.9+
Node.js (for npm scripts)
```

### Installation
```bash
git clone <repository-url>
cd nova-civilizational-architecture
pip install -r requirements.txt
export JWT_SECRET=dev  # For testing
```

### Verification
```bash
# Run full test suite
python -m pytest -q

# Check system maturity
npm run maturity

# Test enhanced Slot 9 API
python -c "from slots.slot09_distortion_protection.hybrid_api import create_hybrid_slot9_api; print('✅ System ready')"
```

## Process Scope Note

The Semantic Mirror operates **in-process** - each CLI invocation starts with an empty mirror state. This is by design for security and isolation.

**For live visibility:**
- Use `--serve` mode: `python scripts/semantic_mirror_dashboard.py --serve 8787 --watch`
- Or publish a heartbeat: `python -c "from orchestrator.semantic_mirror import publish; publish('slot07.heartbeat', {'tick':1}, 'slot07_production_controls', ttl=120.0)"`

If you see `active=0` in compact mode, this indicates a stateless probe. Use the above methods to show live activity.

## 🏗️ Architecture Overview

### 10-Slot Civilizational Framework

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Slot 1    │  │   Slot 2    │  │   Slot 3    │  │   Slot 4    │  │   Slot 5    │
│Truth Anchor │  │ΔTHRESH Mgr  │  │Emotional    │  │TRI Engine   │  │Constellation│
│    (4.0)    │  │   (4.0)     │  │Matrix (2.0) │  │   (3.0)     │  │Nav (2.0)    │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
        │                │                │                │                │
        └────────────────┼────────────────┼────────────────┼────────────────┘
                         │                │                │
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Slot 6    │  │   Slot 7    │  │   Slot 8    │  │   Slot 9    │  │  Slot 10    │
│Adaptive     │  │Production   │  │Memory & IDS │  │Distortion   │  │Deployment   │
│Synthesis    │  │Controls     │  │Protection   │  │Protection   │  │& Modeling   │
│   (4.0)     │  │   (2.0)     │  │   (3.0)     │  │   (4.0)     │  │   (3.0)     │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

### Core Components

- **🎯 Truth Anchor System**: Cryptographic reality verification with RealityLock
- **⚡ ΔTHRESH Integration**: Advanced pattern detection and TRI calculation  
- **🛡️ Hybrid API**: Enterprise-grade distortion protection (v3.1.0)
- **🔄 Orchestrator**: Async event-driven coordination layer
- **📊 IDS Integration**: Integrity Detection System for stability monitoring

## 🔧 Recent Enhancements

### ✨ Latest Updates (2025-09-08)
- **🔌 Plugin Architecture**: Config-driven slot enable/disable with contract-based routing
- **🎯 Slot 6 Production Enhancement**: Complete legacy retirement strategy with environment gates
- **🧪 Contract Testing**: Schema freeze tests prevent breaking changes to CULTURAL_PROFILE@1
- **📊 Observability**: Decision metrics and legacy usage tracking via `/health/config`
- **🚀 CI/CD Matrix**: Dual testing (standard + legacy-blocked) for controlled migration

### Slot 6 API Deprecation Timeline
- **Current (v7.4.1)**: Legacy `multicultural_truth_synthesis` available with warnings; `NOVA_BLOCK_LEGACY_SLOT6` enables hard block
- **Next Release**: CI defaults to `NOVA_BLOCK_LEGACY_SLOT6=1`; legacy compatibility job maintained
- **Following Release**: Legacy module removed entirely; clean new API only

**Migration Path**: Use `engine.CulturalSynthesisEngine` and `adapter.CulturalSynthesisAdapter` instead of legacy classes.

### Plugin System
Slots are now plugins with config-driven enable/disable. Enable specific slots with:
```bash
export NOVA_SLOTS="slot02,slot04,slot06,slot10"
```

**Contract-Based Routing:**
- `TRI_REPORT@1` (slot04 → slot02/slot05)
- `CULTURAL_PROFILE@1` (slot06 → slot10) 
- `DETECTION_REPORT@1` (slot02 → slot05/slot09)
- `CONSTELLATION_STATE@1` (slot05 → slot09)

Missing producers degrade gracefully via NullAdapters. Plugin status and contracts available at `/health/config`.

### ✨ Previous Updates (2025-09-06)
- **🎉 Resolved GitHub conflicts**: Successfully merged enhanced Slot 9 features
- **🔄 Pydantic v2 Migration**: Complete compatibility upgrade for modern CI/CD
- **🌟 Enhanced Hybrid API**: Added hash chain audit trails, deployment feedback system
- **🧹 System Cleanup**: Removed 587 temporary files, optimized repository size
- **📈 Maturity Boost**: Updated assessment shows significant progress

### 🛠️ Technical Improvements
- **Version Control Fields**: Added `format_version`, `api_version`, `compatibility_level`
- **Enhanced Policy Actions**: Extended monitoring and deployment-specific options
- **Cryptographic Audit Trails**: SHA-256 hash chaining for compliance
- **Deployment Feedback Loop**: Slot 10 integration for outcome tracking
- **Error Handling**: Comprehensive error_details with structured codes

## 📦 Dependencies

### Core Dependencies
```
Flask==2.3.3
PyYAML==6.0.2
pydantic>=2,<3
fastapi>=0.104.0
pytest>=7.0.0
```

### Development Tools
```bash
# Maturity assessment
npm run maturity

# Quick testing  
pytest -q

# Slot-specific testing
pytest -q slots/slot02_deltathresh
```

## 🔐 Security & Production

### Environment Configuration
```bash
# Required for testing
export JWT_SECRET=dev

# Optional features
export NOVA_SLOT10_ENABLED=true
export NOVA_GM_ENABLED=true
export NOVA_LOG_LEVEL=INFO
```

### Production Deployment
```bash
# With Slot 10 deployment
python app.py --deploy "MIT_AI_Lab" --type academic

# API server mode
python -c "
from slots.slot09_distortion_protection.hybrid_api import create_fastapi_app, create_hybrid_slot9_api
app = create_fastapi_app(create_hybrid_slot9_api())
import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)
"
```

## 🧪 Testing & Quality

### Test Coverage
- **161 tests passing** ✅
- **2 tests skipped** (expected)
- **Property-based testing** with Hypothesis
- **Integration tests** for all slots
- **Performance benchmarks**

### Quality Tools
- **Static Analysis**: Type checking, linting
- **Maturity Assessment**: Automated scoring system
- **Circuit Breakers**: Production resilience patterns
- **Health Monitoring**: Comprehensive system observability

## 🔒 Governance & CI Protection

### Branch Protection
**Main branch** is protected with required status checks and code review:
- **Required Checks**: `nova-ci` (full test suite), `health-config-matrix` (smoke tests), `IDS CI`
- **CODEOWNERS Protection**: Changes to `contracts/`, `.github/workflows/`, and docs require approval
- **No Direct Pushes**: All changes flow through pull requests with review

### Health Test Strategy
- **Health Matrix**: Runs lightweight smoke tests (`@pytest.mark.health`) across Python 3.10/3.11/3.12 
- **Guard Protection**: Matrix job fails if >15 tests collected (prevents scope drift)
- **Test Selection**: `pytest -m health --ignore=tests/contracts` keeps health matrix fast
- **Contract Testing**: Full contract validation runs in main CI with `jsonschema` dependency

### Schema Change Process
- **Provenance Tracking**: Slot 3 & 6 emit `schema_id` + `schema_version` in `/health` endpoint
- **Centralized Management**: Schema versions managed in `orchestrator/contracts/provenance.py`
- **Contract Evolution**: Use `CONTRACT:BUMP` labels for schema changes, update `SCHEMA_VERSION`
- **Freeze Protection**: `contracts-freeze.yml` prevents accidental breaking changes

### Adding Health Tests
```python
import pytest

@pytest.mark.health  # Required marker for health matrix inclusion
def test_my_health_check():
    # Fast smoke test only - no heavy operations
    pass
```

## 🗺️ Development Roadmap

### Next Phase Priorities
1. **Advance Relational → Structural**: Enhance Slots 3, 5, 7
2. **Complete Processual Migration**: Add adaptive processing to Slots 4, 8, 10
3. **Expand Test Coverage**: Comprehensive testing for all slots
4. **Multi-AI Integration**: Deeper collaboration workflows
5. **Performance Optimization**: Scaling for civilizational deployment

### Multi-AI Collaboration Opportunities
- **Code Review Cycles**: Each AI contributes domain expertise
- **Pattern Recognition**: Cross-validation of architectural decisions  
- **Optimization Strategies**: Diverse approaches to performance challenges
- **Quality Assurance**: Multi-perspective testing and validation
- **Documentation**: Comprehensive system understanding from multiple viewpoints

## 📚 Documentation

- **📖 [CLAUDE.md](CLAUDE.md)**: AI development standards and commands
- **📊 [docs/maturity.yaml](docs/maturity.yaml)**: Detailed maturity assessment
- **🔧 [package.json](package.json)**: NPM scripts for development workflow
- **⚡ API Documentation**: Available at `/docs` when running FastAPI server

## 🤝 Contributing

This is a **multi-AI collaborative project** coordinated by **Pavlos Kolivatzis**. Each AI system contributes according to its strengths:

1. **Architecture Design**: System-level thinking and integration
2. **Code Implementation**: Algorithm development and optimization  
3. **Testing & Validation**: Quality assurance and edge case handling
4. **Documentation**: Comprehensive explanation and maintenance guides
5. **Performance Analysis**: Scaling and optimization strategies

### Multi-AI Analysis Template
Use this prompt for system analysis across different AI platforms:

```markdown
# NOVA System Analysis - [AI_NAME] Perspective
Analyze this civilizational architecture codebase and provide:
1. Overall maturity assessment (0-4 scale)
2. Critical findings and recommendations  
3. Unique insights from your AI perspective
4. Collaboration opportunities with other AI systems
```

## 🌟 Project Philosophy

> **"Building civilizational-scale AI systems requires civilizational-scale collaboration - not just between humans, but between diverse AI intelligences, each contributing their unique strengths toward a common goal of beneficial, robust, and scalable technology."**  
> *— Pavlos Kolivatzis*

This project demonstrates that multi-AI collaboration, under human coordination, can produce more resilient, comprehensive, and innovative solutions than any single AI system working alone.

## 📄 License & Credits

**Project Creator & Coordinator**: Pavlos Kolivatzis  
**AI Collaborators**: Claude, Codex-GPT, DeepSeek, Gemini, Copilot  
**Maintainer**: Pavlos Kolivatzis (docs/maturity.yaml)

---

**Status**: Production-Ready | **Maturity**: 3.1/4.0 | **Tests**: ✅ 161 passing | **Multi-AI**: 5 systems contributing

*Created and coordinated by Pavlos Kolivatzis with collaboration between Claude, Codex-GPT, DeepSeek, Gemini, and Copilot*