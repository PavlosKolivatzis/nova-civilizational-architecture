# NOVA Civilizational Architecture 🌟

![CI](https://github.com/PavlosKolivatzis/nova-civilizational-architecture/actions/workflows/nova-ci.yml/badge.svg)
![Health Matrix](https://github.com/PavlosKolivatzis/nova-civilizational-architecture/actions/workflows/health-config-matrix.yml/badge.svg)
![Status](https://img.shields.io/badge/maturity-4.0_⭐-1f8b4c)
![Coverage](https://img.shields.io/badge/slots-10%2F10_processual-1f8b4c)

> **Multi-AI Collaborative Project** created and coordinated by **Pavlos Kolivatzis**
> Built through cooperation between Claude, Codex-GPT, DeepSeek, Gemini, and Copilot

> **🎉 MILESTONE:** **Phase 6.0 Probabilistic Belief Propagation** complete! Nova now features **uncertainty quantification** with belief state propagation across the Cognitive-Operational-Ethical Trinity. System maturity: **6.0/4.0** with probabilistic intelligence ⚡

## 🎯 Overview
Production-grade multicultural truth synthesis engine with 10-slot cognitive architecture for civilizational-scale deployment. This system represents a groundbreaking approach to AI-assisted civilizational development through modular, resilient architecture.

**Current Status**: System Maturity **4.1/4.0** | **700 tests passing** | **ALL 10 slots at Processual (4.0) level** ⭐

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
🎯 PHASE 4.1 COMPLETE: SLOT-SPECIFIC MEMORY METABOLISM ⚡
Overall Maturity: 4.1/4.0 — Adaptive Intelligence Circuit Active ⭐

🆕 Phase 4.1 Features:
• Slot-specific anomaly weighting curves (5 specialized slot profiles)
• Dynamic TRI-aware half-life adaptation for context preservation
• Slot7↔Slot6 reflex back-pressure coordination during system stress
• Slot10 deployment feedback loops closing adaptive learning circuit
• Civilizational memory metabolism with contextual intelligence

📜 Phase 4 Features:
• EWMA + hysteresis anomaly detection with intelligent pulse weighting
• Thread-safe anomaly scoring with concurrent access patterns
• Intelligent pulse weight multipliers (1.0-3.0x) during system stress
• TRI inputs sourced via semantic mirror contexts (e.g., `slot04.tri_drift_z`, `slot04.phase_jitter`)
• Real-time Grafana monitoring dashboard (7 panels)

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
• Total: 200+ new Phase 4 tests across 706 total system tests
```

## Directory Legend

- `src/nova/slots/slotXX_*`: canonical runtime modules for each slot
- `slots/slotXX_*`: compatibility shims retained for legacy imports
- `docs/slots/slotXX/`: slot-specific design and operations documentation
- `docs/architecture/`: cross-slot architecture and flow references
- `docs/reports/`: audits, coverage, risk, and testing overviews
- `archive/legacy-slot-migration/`: historical documentation covering the pre-namespaced layout

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

# Install dependencies (wheel-only for CVE-2025-8869 mitigation)
pip install --only-binary :all: -r requirements.txt

export JWT_SECRET=dev  # For testing
```

> **Security Note**: We enforce `--only-binary :all:` to mitigate [CVE-2025-8869](SECURITY.md#def-010-pip-252-tarfile-link-escape-cve-2025-8869) in pip 25.2. Remove flag after upgrading to pip 25.3+.

### Verification
```bash
# Run full test suite
python -m pytest -q

# Check system maturity
npm run maturity

# Test enhanced Slot 9 API
python -c "from nova.slots.slot09_distortion_protection.hybrid_api import create_hybrid_slot9_api; print('✅ System ready')"
```

### One-liner: run Nova with Phase 4 enabled
```bash
# Production metrics correctness (singleton required for counter accuracy)
export NOVA_ENABLE_PROMETHEUS=1 \
  NOVA_UNLEARN_ANOMALY=1 \
  NOVA_SMEEP_INTERVAL=15
# uvicorn must run single-worker for accurate counter metrics
python -m uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000 --workers 1
```

**Cross-platform variants:**
```powershell
# PowerShell
$env:NOVA_ENABLE_PROMETHEUS=1; $env:NOVA_UNLEARN_ANOMALY=1; $env:NOVA_SMEEP_INTERVAL=15
uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000 --workers 1
```

```bat
# Windows cmd
set NOVA_ENABLE_PROMETHEUS=1 && set NOVA_UNLEARN_ANOMALY=1 && set NOVA_SMEEP_INTERVAL=15
uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000 --workers 1
```

### 📊 Phase 4 Monitoring Setup

Enable real-time monitoring and anomaly-aware unlearning:

```bash
# Enable Prometheus metrics and anomaly detection
export NOVA_ENABLE_PROMETHEUS=1
export NOVA_UNLEARN_ANOMALY=1

# Start Nova with monitoring enabled
python -m uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000

# In another terminal, start standalone Prometheus
cd monitoring && python standalone-prometheus.py

# Verify metrics endpoint
curl http://localhost:8000/metrics | grep nova_unlearn_anomaly
```

**PromQL tips (post-counter migration):**
- Use `increase()` or `rate()` for:
  - `nova_unlearn_pulses_sent_total`
  - `nova_entries_expired_total`
  - `nova_unlearn_pulse_to_slot_total`
  - `nova_slot6_decay_events_total`
  - `nova_slot6_decay_amount_total`
  - `nova_fanout_delivered_total`
  - `nova_fanout_errors_total`
- Use raw gauges for anomaly state:
  - `nova_unlearn_anomaly_score`
  - `nova_unlearn_anomaly_multiplier`
  - `nova_unlearn_anomaly_engaged`

**Operational SLO checks**
```promql
# Accounting invariant (5m):
sum(increase(nova_unlearn_pulse_to_slot_total[5m]))
  == increase(nova_unlearn_pulses_sent_total[5m])

# Fanout errors should be zero (5m):
increase(nova_fanout_errors_total[5m]) == 0

# Decay activity should be present during active periods (5m):
increase(nova_slot6_decay_events_total[5m]) > 0

# Anomaly engaged for sustained period (≥ 3 of last 5 minutes):
avg_over_time(nova_unlearn_anomaly_engaged[5m]) >= 0.6
```

**Dashboard Setup:**
- Import `monitoring/grafana/dashboards/nova-phase4-anomaly-weighting.json` into Grafana
- View 7 real-time panels: anomaly score, weight multiplier, engagement state, pulse rates, decay events
- Monitor intelligent pulse weighting during system stress (1.0-3.0x multipliers)

**Environment Variables (Phase 4 — Anomaly Detection):**
```bash
# Master switch
export NOVA_UNLEARN_ANOMALY=1

# EWMA + hysteresis controls (defaults shown)
export NOVA_UNLEARN_ANOM_ALPHA=0.30     # EWMA smoothing factor
export NOVA_UNLEARN_ANOM_TAU=1.00       # Engage threshold (score > TAU)
export NOVA_UNLEARN_ANOM_MARGIN=0.20    # Disengage margin (below TAU-MARGIN)
export NOVA_UNLEARN_ANOM_GAIN=0.50      # Linear gain above TAU
export NOVA_UNLEARN_ANOM_CAP=3.00       # Max multiplier
export NOVA_UNLEARN_ANOM_WIN=5          # Window length for breaches
export NOVA_UNLEARN_ANOM_REQ=3          # Required breaches in window to engage

# Phase 4.1: Slot-specific weighting curves
export NOVA_SLOT06_W_TRI=0.7            # Cultural synthesis: high TRI sensitivity
export NOVA_SLOT07_W_PRESS=0.8          # Production controls: high pressure response
export NOVA_SLOT10_W_JITTER=0.3         # Deployment: jitter sensitivity
export NOVA_UNLEARN_MIN_HALF_LIFE=60    # Dynamic half-life bounds (1 min)
export NOVA_UNLEARN_MAX_HALF_LIFE=1800  # Dynamic half-life bounds (30 min)
export NOVA_SLOT07_REFLEX_THRESHOLD=0.70 # Slot7 back-pressure threshold
export NOVA_SLOT07_REFLEX_SLOPE=1.50    # Pressure → back-pressure mapping

# Monitoring & metrics
export NOVA_ENABLE_PROMETHEUS=1
export NOVA_SMEEP_INTERVAL=15   # Semantic mirror sweeper interval (seconds)

# Testing & Development
export NOVA_ALLOW_EXPIRE_TEST=1
export NOVA_EXPIRE_TEST_AGE=120
export NOVA_UNLEARN_CANARY=0    # Off by default in prod
# NDJSON rotation (if enabled)
export NOVA_UNLEARN_LOG_MAX_BYTES=10485760
export NOVA_UNLEARN_LOG_BACKUPS=5
```

> Note: The variable is intentionally `NOVA_SMEEP_INTERVAL` (matches code), not "SWEEP".

### 🚨 Phase 4 Troubleshooting

**Common Issues:**
- **No anomaly gauges?** Ensure `NOVA_UNLEARN_ANOMALY=1` is set
- **No unlearn pulses?** Ensure TTL ≥ 60s and access_count > 1 on contexts
- **Counters look doubled?** Confirm single worker (`--workers 1`), see singleton guard above
- **Dashboard shows no data?** Verify Prometheus scraping `http://localhost:8000/metrics`
- **Engaged state stuck?** Check `nova_unlearn_anomaly_score` - may need time to decay below threshold

## Process Scope Note

The Semantic Mirror operates **in-process** - each CLI invocation starts with an empty mirror state. This is by design for security and isolation. Prometheus and the sweeper read the same in-process singleton; run Nova as a long-lived service for stable metrics.

**For live visibility:**
- Use `--serve` mode: `python scripts/semantic_mirror_dashboard.py --serve 8787 --watch`
- Or publish a heartbeat: `python -c "from orchestrator.semantic_mirror import publish; publish('slot07.heartbeat', {'tick':1}, 'slot07_production_controls', ttl=120.0)"`

If you see `active=0` in compact mode, this indicates a stateless probe. Use the above methods to show live activity.

## 🏗️ Architecture Overview

### Nova Slot Network — Multi-Layer Autonomous Architecture ⭐

#### **🎯 All 10 Slots at Processual (4.0) Maturity**
```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Slot 1    │  │   Slot 2    │  │   Slot 3    │  │   Slot 4    │  │   Slot 5    │
│Truth Anchor │  │ΔTHRESH Mgr  │  │Emotional    │  │TRI Engine   │  │Constellation│
│  ⭐ (4.0)    │  │  ⭐ (4.0)    │  │Matrix⭐(4.0)│  │  ⭐ (4.0)    │  │Nav ⭐ (4.0) │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘

┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Slot 6    │  │   Slot 7    │  │   Slot 8    │  │   Slot 9    │  │  Slot 10    │
│Cultural     │  │Production   │  │Memory & IDS │  │Distortion   │  │Civilizational│
│Synthesis    │  │Controls     │  │Protection   │  │Protection   │  │ Deployment  │
│  ⭐ (4.0)    │  │  ⭐ (4.0)    │  │  ⭐ (4.0)    │  │  ⭐ (4.0)    │  │  ⭐ (4.0)    │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

#### **🌊 Multi-Layer Network Architecture**

**Layer 1: Contract Network** (Semantic Information Flow)
```
S3 → S6 → S10  (Emotional → Cultural → Deployment)
S3 → S4        (Emotional → TRI Processing)
S6 → S2        (Cultural → Threshold Management)
S5 → S9        (Constellation → Distortion Defense)
S3,S8,S9 → S7  (Multi-Input Production Control Hub)
```

**Layer 2: Flow Fabric** (Adaptive Routing with Dynamic Weight/Frequency)
```
AdaptiveLinks: EMOTION_REPORT@1, CULTURAL_PROFILE@1, TRI_REPORT@1
• Automatic load balancing based on downstream capacity
• Prometheus metrics: adaptive_link_weight, adaptive_link_frequency
• Real-time adaptation: 0.1-5.0x frequency, 0.1-3.0x weight modulation
```

**Layer 3: Reflex System** (Upstream Throttling & Backpressure)
```
S7 Reflex Emitter → ReflexBus → Contract Throttling
• Circuit breaker pressure → throttle S3→S6 emotional processing
• Memory pressure → modulate S6→S10 cultural deployment
• Integrity violations → clamp S3→S4 TRI processing
```

**Layer 4: Health Monitoring** (Real-time State Awareness)
```
S10 ← S8,S4 Health Feeds (deployment gate decisions)
S8: integrity_score, quarantine_active, recent_recoveries
S4: safe_mode_active, drift_z (O(1) rolling statistics)
```

#### **🎭 Network Roles & Capabilities**

**Information Producers:**
- **Slot 3**: Primary cognitive source (4 output contracts)
- **Slot 6**: Cultural synthesis hub (connects to S2, S10)
- **Slot 5**: Pattern detection (feeds distortion protection)

**Integration Hubs:**
- **Slot 7**: Production control center ⭐ (5 input contracts, reflex coordination)
- **Slot 10**: Deployment orchestrator (2 contracts + 2 health feeds + cross-slot coordination)

**Autonomous Processors:**
- **Slots 4,8**: Self-healing with MTTR guarantees (≤5s recovery, ≤10s rollback)
- **Slot 9**: Distortion detection with constellation awareness
- **Slot 1**: Truth anchoring (stability foundation)

#### **🚀 Civilizational-Scale Features**
- **Cross-Slot Coordination**: S10 manages state across S8,S4 for deployment safety
- **Cultural Governance**: S6 provides ethical constraints for S10 civilizational deployment
- **Adaptive Intelligence**: Flow Fabric adjusts routing based on real-time conditions
- **Self-Healing**: Multi-layer fault tolerance with autonomous recovery
- **Truth Verification**: S1,S4 maintain reality anchoring across all cognitive processes

### Core Components

- **🎯 Truth Anchor System**: Cryptographic reality verification with autonomous recovery
- **⚡ ΔTHRESH Integration**: Advanced pattern detection with cultural profile integration
- **🛡️ Autonomous Protection**: Multi-layer defense (memory, distortion, integrity)
- **🌊 Flow Fabric**: Adaptive routing with real-time weight/frequency adjustment
- **🔄 Orchestrator**: Event-driven coordination with reflex system integration
- **📊 Health Monitoring**: Live feeds with MTTR ≤5s recovery guarantees
- **🎭 Cross-Slot Coordination**: Civilizational deployment with autonomous rollback

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
## Phase-2 Feature Flags & Observability

| Flag                   | Default | Scope            | Effect when enabled                          |
|------------------------|---------|------------------|----------------------------------------------|
| `NOVA_ENABLE_TRI_LINK` | off     | Slots 4↔5        | TRI→Constellation integration active         |
| `NOVA_ENABLE_LIFESPAN` | off     | Web (ASGI)       | Lifespan manager handles startup/shutdown    |
| `NOVA_USE_SHARED_HASH` | off     | Slots 9 & 10     | Use shared blake2b audit hash if available   |

**Observability:** Slot7 exposes current states under `metrics.feature_flags`:
```json
{
  "tri_link_enabled": false,
  "lifespan_enabled": true,
  "shared_hash_enabled": true,
  "shared_hash_available": true,
  "effective_hash_method": "shared_blake2b"
}
```

**CI lanes:** see `.github/workflows/phase2-features.yml` for per-flag validation.

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
python -m pytest tests/test_slot02_deltathresh.py -q
```

> Note: Source packages now live under `src/nova/`; prefer imports like `from nova.slots.slotXX...` when running examples.

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
from nova.slots.slot09_distortion_protection.hybrid_api import create_fastapi_app, create_hybrid_slot9_api
app = create_fastapi_app(create_hybrid_slot9_api())
import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)
"
```

## 🧪 Testing & Quality

### Test Coverage
- **706 tests passing** ✅ (including 200+ Phase 4 tests)
- **3 tests skipped** (expected)
- **Property-based testing** with Hypothesis
- **Integration tests** for all slots
- **Performance benchmarks**
- **Chaos engineering** with weekly automated validation

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

### ✅ Phase 3 COMPLETE: All Slots Processual (4.0)
**MILESTONE ACHIEVED**: First fully autonomous Nova system with all 10 cognitive slots at Processual maturity.

### Phase 4+ Priorities
1. **Advanced Flow Mesh**: Enhanced inter-slot coordination and data flows
2. **Multi-Tenant Operation**: Isolated autonomous domains for multiple deployments
3. **Extended Chaos Engineering**: Long-term reliability validation and stress testing
4. **Civilizational Integration**: Real-world deployment patterns and scaling validation
5. **Advanced Observability**: Enhanced metrics, alerting, and operational intelligence

### Multi-AI Collaboration Opportunities
- **Code Review Cycles**: Each AI contributes domain expertise
- **Pattern Recognition**: Cross-validation of architectural decisions  
- **Optimization Strategies**: Diverse approaches to performance challenges
- **Quality Assurance**: Multi-perspective testing and validation
- **Documentation**: Comprehensive system understanding from multiple viewpoints

## 📚 Documentation

- **📖 [CLAUDE.md](CLAUDE.md)**: AI development standards and commands
- **📊 [docs/maturity.yaml](docs/maturity.yaml)**: Detailed maturity assessment (v3.0 - All slots Processual)
- **🎉 [docs/releases/2025-09-phase-3.md](docs/releases/2025-09-phase-3.md)**: Phase 3 completion release notes
- **⚡ [docs/autonomy_artifact_v1_1.md](docs/autonomy_artifact_v1_1.md)**: Light-Clock Temporal Coherence System (ΔC-LIGHTCLOCK)
- **🔗 [META_LENS_TETHER_CONFIRMATION.md](META_LENS_TETHER_CONFIRMATION.md)**: Architectural Integration Verification (META_LENS_REPORT@1)
  *"CONFIRMED: META_LENS_REPORT@1 is a native architectural extension of Slot 2 (ΔTHRESH Manager), using only existing flows and governance, with instant rollback capability."*
- **🎯 [docs/releases/2025-09-meta-lens-canary.md](docs/releases/2025-09-meta-lens-canary.md)**: META_LENS Canary Deployment Results
- **👁️ [docs/ops/observability.md](docs/ops/observability.md)**: Comprehensive observability guide
- **📝 [CHANGELOG.md](CHANGELOG.md)**: Version history and milestone tracking
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

### Phase 6.0 – Probabilistic Belief Propagation (Sealed)
Completed: 2025-10-19 • Tag: v6.0-belief-propagation • Commit: c3bab48
Implements cross-slot uncertainty quantification (TRI ↔ Controls)
Status: Golden → Sealed → Archived • Integrity Chain Unbroken

**Status**: Production-Ready | **Maturity**: 6.0/4.0 ⭐ | **Tests**: ✅ 706 passing | **Autonomy**: All 10 slots Processual

*Created and coordinated by Pavlos Kolivatzis with collaboration between Claude, Codex-GPT, DeepSeek, Gemini, and Copilot*
