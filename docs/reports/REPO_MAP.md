# Nova Civilizational Architecture - Repository Map

**Generated:** 2025-10-04 05:20 EET
**Baseline Commit:** b4d1793349181ab4e5c02ad4e8c66d5f01e9a3f9
**Branch:** audit/system-cleanup-v1

---

## Repository Overview

**Total Files:** 553 tracked files (excluding venv, node_modules, __pycache__)
- Python: 378 files
- Markdown: 84 files
- YAML: 42 files (.yml + .yaml)
- JSON: 34 files
- PowerShell: 10 scripts
- Shell: 4 scripts

---

## Top-Level Structure

```
nova-civilizational-architecture/
├── src/                  # Primary package root
│   └── nova/             # Namespaced runtime (slots, loader, auth)
├── slots/                # Legacy import shims (read-only)
├── orchestrator/         # Core orchestration logic
├── tests/                # Comprehensive test suite (24 subdirectories)
├── scripts/              # Operational scripts (health, chaos, validation)
├── docs/                 # Documentation
├── config/               # Configuration files
├── api/                  # API layer
├── .github/              # CI/CD workflows
└── [root configs]        # pytest.ini, requirements.txt, etc.
```

---

## Slots (Slot01-Slot10)

**Location:** `src/nova/slots/` (legacy shims remain under `slots/`)

| Slot | Directory | Purpose | Status |
|------|-----------|---------|--------|
| 01 | `slot01_truth_anchor` | Truth Anchor System | 🔍 TO AUDIT |
| 02 | `slot02_deltathresh` | Delta-Threshold Detection | 🔍 TO AUDIT |
| 03 | `slot03_emotional_matrix` | Emotional Analysis | 🔍 TO AUDIT |
| 04a | `slot04_tri` | TRI Engine (Operational - Engine 1) | ✅ DUAL-ENGINE ARCHITECTURE |
| 04b | `slot04_tri_engine` | TRI Engine (Content - Engine 2) | ✅ DUAL-ENGINE ARCHITECTURE |
| 05 | `slot05_constellation` | Constellation Mapping | 🔍 TO AUDIT |
| 06 | `slot06_cultural_synthesis` | Cultural Synthesis | 🔍 TO AUDIT |
| 07 | `slot07_production_controls` | Production Controls | 🔍 TO AUDIT |
| 08a | `slot08_memory_ethics` | Memory Ethics (Legacy) | ✅ MIGRATION-READY ARCHITECTURE |
| 08b | `slot08_memory_lock` | Memory Lock (Processual 4.0) | ✅ MIGRATION-READY ARCHITECTURE |
| 09 | `slot09_distortion_protection` | Distortion Protection | 🔍 TO AUDIT |
| 10 | `slot10_civilizational_deployment` | Deployment Engine | 🔍 TO AUDIT |

**Common Modules:**
- `src/nova/slots/common/` - Shared utilities
- `src/nova/slots/config/` - Slot configuration management

**FINDINGS:**
- ✅ **SLOT 4 DUAL-ENGINE**: Intentional architecture - Engine 1 (operational monitoring) + Engine 2 (content analysis)
  - Routing via `orchestrator/adapters/slot4_tri.py` based on method called
  - Both engines active and tested (see `tests/test_orchestrator_slot4_tri_adapter.py`)
- ✅ **SLOT 8 MIGRATION-READY**: Two implementations for phased upgrade path
  - **slot08_memory_ethics** (Legacy): Simple ACL-based protection - CURRENTLY USED by orchestrator
  - **slot08_memory_lock** (Processual 4.0): Autonomous self-healing with IDS - NOT YET INTEGRATED
  - Orchestrator uses `orchestrator/adapters/slot8_memory_ethics.py` (imports legacy only)
  - Migration path documented in `slot08_memory_lock/README.md:399-410`

---

## Orchestrator

**Location:** `/orchestrator/`

| Module | Purpose | Files | Status |
|--------|---------|-------|--------|
| `core/` | Core orchestration logic | TBD | 🔍 TO AUDIT |
| `adapters/` | Slot adapters | TBD | 🔍 TO AUDIT |
| `contracts/` | Contract definitions | TBD | 🔍 TO AUDIT |
| `plugins/` | Plugin system | TBD | 🔍 TO AUDIT |
| `router/` | Request routing | TBD | 🔍 TO AUDIT |

**Key Files (To Be Inventoried):**
- `app.py` - FastAPI application entry point
- `semantic_mirror.py` - Semantic Mirror implementation
- `flow_fabric_init.py` - Flow Fabric initialization
- `prometheus_metrics.py` - Metrics export
- `reflection.py` - Reflection endpoint
- `unlearn_weighting.py` - Unlearn weighting logic

---

## Tests

**Location:** `/tests/`

**Test Directories (24 total):**

| Category | Directories | Purpose |
|----------|-------------|---------|
| **API** | `api/`, `web/` | API and web interface tests |
| **Unit** | `orchestrator/`, `orch/`, `router/` | Orchestrator unit tests |
| **Integration** | `integration/`, `e2e/` | Integration and end-to-end tests |
| **Slot-Specific** | `slot06/`, `slot07/`, `slot10/` | Slot-specific test suites |
| **Contracts** | `contracts/`, `flow/` | Contract and flow fabric tests |
| **Quality** | `health/`, `meta/`, `config/` | Health checks and metadata tests |
| **Performance** | `perf/`, `performance/`, `slo/` | Performance and SLO tests |
| **Robustness** | `chaos/`, `concurrency/`, `security/` | Chaos, concurrency, security tests |
| **Advanced** | `property/`, `metrics/`, `plugins/` | Property-based, metrics, plugins tests |

**Test Coverage Target:** ≥85% overall, 100% on critical gates

---

## Scripts

**Location:** `/scripts/`

**Operational Scripts (18 total):**

| Script | Type | Purpose |
|--------|------|---------|
| `health_verification.py` | Health | Comprehensive health check |
| `comprehensive_health_check.py` | Health | Full system health verification |
| `local_health_check.sh` | Health | Local health check (shell) |
| `sanity_check.py` | Health | Quick sanity verification |
| `semantic_mirror_dashboard.py` | Monitor | Semantic Mirror monitoring dashboard |
| `semantic_mirror_quick_asserts.py` | Validation | Quick assertions for Semantic Mirror |
| `semantic_mirror_flip.py` | Ops | Semantic Mirror flip operations |
| `semantic_mirror_loadgen.py` | Test | Load generation for Semantic Mirror |
| `anr_daily_report.py` | ANR | Adaptive Neural Refinement daily reporting |
| `anr_validate.py` | ANR | ANR validation |
| `slot8_chaos_simple.py` | Chaos | Slot 8 chaos testing |
| `slot8_corruption_replay.py` | Chaos | Slot 8 corruption replay |
| `slot10_weekly_chaos.py` | Chaos | Slot 10 weekly chaos testing |
| `diagnose_creativity_reflect.py` | Debug | Creativity system diagnostics |
| `journal_reflection.py` | Journal | Reflection journaling |
| `validate-schemas.py` | Validation | Schema validation |
| `verify_pilot_ready.py` | Validation | Pilot readiness verification |
| `start_server_test.ps1` | Ops | Server startup test (PowerShell) |

---

## Runtime Entrypoints

### Primary Entrypoint
**File:** `orchestrator/app.py`
**Type:** FastAPI application
**Command:** `uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000`

**Key Endpoints (To Be Verified):**
- `/health` - Health check
- `/metrics` - Prometheus metrics
- `/reflection` - Reflection API
- Additional endpoints TBD

### Alternative Entrypoints
- Scripts in `/scripts/` for operational tasks
- Test runners via `pytest`

---

## External Dependencies

**Core Framework:**
- fastapi==0.116.1
- uvicorn==0.35.0
- pydantic==2.11.7
- starlette==0.47.3

**HTTP Clients:**
- httpx==0.28.1
- aiohttp==3.12.15

**Testing:**
- pytest==8.4.1
- pytest-cov==7.0.0
- pytest-asyncio==1.1.0
- hypothesis==6.138.14
- coverage==7.10.6

**Data/Config:**
- PyYAML==6.0.2
- python-dotenv==1.1.1
- jsonschema==4.25.1

**Utilities:**
- numpy==2.3.2
- prometheus_client==0.23.1
- PyJWT==2.10.1

**Development:**
- ruff==0.12.11
- mypy==1.17.1

**Full dependency tree:** See `dependency_tree.txt`

---

## Ownership & Maintenance

**CODEOWNERS Status:** 🔍 TO BE CREATED

**Proposed Ownership Structure:**

| Area | Owner(s) | Files |
|------|----------|-------|
| Core Orchestrator | TBD | `orchestrator/core/`, `orchestrator/app.py` |
| Slots 1-3 | TBD | `src/nova/slots/slot01_*/`, `src/nova/slots/slot02_*/`, `src/nova/slots/slot03_*/` |
| Slots 4-6 | TBD | `src/nova/slots/slot04_*/`, `src/nova/slots/slot05_*/`, `src/nova/slots/slot06_*/` |
| Slots 7-10 | TBD | `src/nova/slots/slot07_*/`, `src/nova/slots/slot08_*/`, `src/nova/slots/slot09_*/`, `src/nova/slots/slot10_*/` |
| Flow Fabric | TBD | `orchestrator/flow_fabric*.py`, `orchestrator/contracts/` |
| Testing | TBD | `tests/` |
| CI/CD | TBD | `.github/workflows/` |

---

## Known Issues & Anomalies

### Duplicate Implementations

1. **Slot 4 Duplication:**
   - `slot04_tri/` (828 lines, 11 files)
   - `slot04_tri_engine/` (637 lines, 5 files)
   - **Status:** NEEDS INVESTIGATION
   - **Question:** Are both active? Different purposes? Legacy?

2. **Slot 8 Duplication:**
   - `slot08_memory_ethics/`
   - `slot08_memory_lock/`
   - **Status:** NEEDS INVESTIGATION
   - **Question:** Same as Slot 4 - intentional or legacy?

### Action Items from Phase 0
- [ ] Investigate Slot 4 duplication (slot04_tri vs slot04_tri_engine)
- [ ] Investigate Slot 8 duplication (slot08_memory_ethics vs slot08_memory_lock)
- [ ] Create CODEOWNERS file
- [ ] Map all README.md files and verify claims
- [ ] Document runtime flows and entry points in detail

---

## Next Steps

1. **Phase 1:** Run test suite and capture coverage
2. **Phase 2:** Static analysis (ruff, mypy, bandit, vulture)
3. **Phase 3:** Documentation drift analysis
4. **Phase 4:** Defect triage and fix planning
5. **Phase 5:** Cleanup and quality gate enforcement

---

**Status:** SKELETON - Will be expanded during Phases 1-5
**Last Updated:** 2025-10-04 05:20 EET
**Evidence:** AUDIT_LOG.md#Phase-0
