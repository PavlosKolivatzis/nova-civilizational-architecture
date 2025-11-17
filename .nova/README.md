# Nova Agent Entry Protocol

This directory contains the **active map** of Nova's architecture—metadata that reflects the system's current state and provides navigation for external agents, CLI tools, and human operators.

## Quick Start

```bash
# Human-readable welcome screen
npm run nova:welcome

# Single-line status (for scripts)
npm run nova:status

# Machine-readable JSON (for agents)
npm run nova:json
```

## Files

### `meta.yaml` — System Metadata (Stable)

The canonical navigation index for Nova. Contains:

- **Ontology**: Rule of Sunlight, 3 ledgers, 6 core invariants
- **Learning Path**: 4-phase protocol to understand Nova deeply
- **Slot Map**: Canonical definitions of all 10 slots
- **Runtime Introspection**: Pointers to live state (git, maturity, metrics)
- **Agent Protocol**: How external agents should enter and behave

**Maintenance**: Semi-automated
- Hand-curated: Slot map, learning path, docs links (stable)
- Auto-generated: Runtime state via `tools/nova-welcome.sh` (live)

**Philosophy**: This file demonstrates Nova principles while teaching them:
- **Provenance**: Links to sources of truth (git, maturity.yaml, audit reports)
- **Immutability**: Metadata is versioned; changes produce new commits
- **Observability**: Points to runtime introspection endpoints
- **Reversibility**: No behavioral logic; pure navigation

## Agent Entry Flow

```
1. Agent enters repository
   ↓
2. Runs: npm run nova:welcome
   ↓
3. Reads: .nova/meta.yaml
   ↓
4. Follows: learning_path.phase1_orientation
   (agents/nova_ai_operating_framework.md → docs/architecture.md → docs/slots/*.md)
   ↓
5. Introspects: pytest, npm run maturity, curl /metrics
   ↓
6. Declares: capabilities + consent_profile to Slot10
   ↓
7. Receives: scoped access credentials
   ↓
8. Operates: within sunlight (logged, metered, auditable)
```

## Learning Path Summary

### Phase 1: Orientation (~15 min)
- **Goal**: Understand Nova's mental model
- **Read**: `agents/nova_ai_operating_framework.md`, `docs/architecture.md`, `docs/slots/*.md`
- **Focus**: Rule of Sunlight, 3 ledgers, 6 invariants, slot boundaries

### Phase 2: Introspection (~10 min)
- **Goal**: Probe current system state
- **Read**: `src/nova/slots/*/meta.yaml`, `orchestrator/app.py`
- **Run**: `pytest -q`, `npm run maturity`
- **Verify**: 506 tests passing, maturity 4.0

### Phase 3: Observability (~10 min)
- **Goal**: Understand runtime metrics
- **Read**: `orchestrator/prometheus_metrics.py`, slot metrics
- **Run**: `uvicorn` with `NOVA_ENABLE_PROMETHEUS=1`, `curl /metrics`
- **Verify**: Prometheus metrics exposed

### Phase 4: Change Protocol (~10 min)
- **Goal**: Learn to propose reversible changes
- **Read**: Change policy, pre-merge checklist
- **Experiment**: Add flag, gate behavior, test, verify rollback
- **Verify**: Toggle flag → behavior reverts cleanly

## Runtime State Sources

| Source | Command | Provides |
|--------|---------|----------|
| Git | `git log -1 --format='%h %ai %s'` | Commit, timestamp, phase label |
| Maturity | `npm run maturity` | Overall score (4.0), per-slot maturity, test counts |
| Audit | `.artifacts/audit_master_summary.md` | Latest findings (Phase 16.2, 1 CRIT, 7 CVEs) |
| Tests | `pytest -q -m "not slow"` | Pass count (506) |
| Metrics | `curl localhost:8000/metrics` | Live Prometheus metrics (if flag=1) |
| Flags | `.env.example` | Feature flag registry (NOVA_*) |

## Agent Protocol Rules

1. **Default mode**: Read-only
2. **Consent required**: Request `CONSENT_PROFILE` from Slot10 before writes
3. **Sunlight enforcement**: All actions logged, metered, auditable
4. **No hidden channels**: Failures visible, no silent degradation
5. **Revocable access**: Consent can be withdrawn; handle graceful shutdown

## Self-Introduction Template

When declaring to Slot10:

```yaml
agent_id: "uuid-or-stable-identifier"
capabilities:
  - "code_analysis"
  - "test_generation"
  - "metric_collection"
consent_profile: "CE001.standard"  # or CE002.restricted, or custom
provenance:
  organization: "Example Org"
  version: "1.2.3"
  audit_trail: "https://example.org/audit/agent-xyz"
```

## Cross-Platform Support

| Platform | Command |
|----------|---------|
| Unix/macOS/Git Bash | `bash tools/nova-welcome.sh` |
| Windows PowerShell | `powershell tools/nova-welcome.ps1` |
| Cross-platform | `npm run nova:welcome` (auto-detects) |

## Maintenance

**When to update `meta.yaml`**:
- New slot added/removed
- Docs reorganized
- Major phase transition
- Invariants change
- Learning path evolves

**How to update**:
1. Edit `.nova/meta.yaml` directly
2. Increment `meta.schema_version` if structure changes
3. Add changelog entry
4. Commit with message: `docs(meta): <reason for change>`

**Runtime state** (commit, maturity, tests) is auto-fetched by scripts—no manual updates needed.

## Philosophy

This directory embodies Nova's self-awareness:

> "Nova is a system that knows itself. It can describe its architecture, verify its state, and guide newcomers through its ontology—all while demonstrating the principles it teaches."

The metadata here is not documentation *about* Nova; it is Nova *describing itself*.

---

**See also**:
- `agents/nova_ai_operating_framework.md` — Full operating doctrine
- `docs/architecture.md` — Detailed system architecture
- `docs/INTERSLOT_CONTRACTS.md` — Contract stability model
