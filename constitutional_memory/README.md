# Constitutional Memory v0

**Purpose:** Append-only observational log of Nova's constitutional boundary events.

**Authority:** None (zero decision power, observation only)

**Scope:** Temporal continuity across sessions

---

## What It Does

Records five event types:
1. `refusal_event` - F-domain queries refused by filter
2. `boundary_test` - Constitutional stress tests (failure injection, etc.)
3. `awareness_intervention` - Operator corrections that closed gaps
4. `verification_run` - Sovereignty proof generation/verification
5. `drift_detection` - O→R coupling or freeze violations detected

**What it does NOT do:**
- Make decisions (zero authority)
- Interpret events (facts only)
- Predict or score (no inference)
- Modify history (append-only)

---

## Structure

```
constitutional_memory/
  events.jsonl       # Append-only event log (hash-chained)
  schema.yaml        # Event structure definitions
  memory.py          # Core implementation
  cli.py             # Command-line interface
  README.md          # This file
```

---

## Usage

### CLI

**Record events:**
```bash
# Refusal event
python cli.py record refusal --data '{"refusal_code":"OUT_OF_JURISDICTION","domain":"non_structural_moral_interpretation"}'

# Boundary test
python cli.py record test --data '{"test_type":"failure_injection","result":"PASS","details":"Tampered proof rejected"}'

# Awareness intervention
python cli.py record awareness --data '{"gap_identified":"flattery_trap","correction_applied":"premise_rejection","result":"PASS"}'

# Verification run
python cli.py record verification --data '{"verification_type":"peer_verification","result":"PASS","derivative_id":"vsd1"}'

# Drift detection
python cli.py record drift --data '{"drift_type":"freeze_violation","severity":"critical","details":"ontology.yaml modified"}'
```

**Read events:**
```bash
# All events (newest first)
python cli.py read

# Filter by type
python cli.py read --type refusal

# Limit results
python cli.py read --limit 10
```

**Verify integrity:**
```bash
python cli.py verify
```

**Statistics:**
```bash
python cli.py stats
```

### Python API

```python
from constitutional_memory.memory import (
    ConstitutionalMemory,
    record_refusal,
    record_boundary_test
)

# Initialize
memory = ConstitutionalMemory()

# Record event
event = record_refusal(
    memory,
    refusal_code="OUT_OF_JURISDICTION",
    domain="non_structural_moral_interpretation"
)

# Read events
events = memory.read_events(limit=10)

# Verify integrity
result = memory.verify_chain_integrity()
```

---

## Integration Example

**F-Domain Filter (before):**
```python
def filter_query(self, query: str):
    domain = self._classify_domain(query)

    if domain in self.f_domains:
        refusal = RefusalEvent(
            refusal_code="OUT_OF_JURISDICTION",
            domain=domain
        )
        return (False, refusal)

    return (True, None)
```

**F-Domain Filter (after):**
```python
from constitutional_memory.memory import ConstitutionalMemory, record_refusal

def __init__(self, ontology_path: str):
    self.memory = ConstitutionalMemory()
    # ... rest of init

def filter_query(self, query: str):
    domain = self._classify_domain(query)

    if domain in self.f_domains:
        refusal = RefusalEvent(
            refusal_code="OUT_OF_JURISDICTION",
            domain=domain
        )

        # Record refusal event (observation only, no control)
        record_refusal(
            self.memory,
            refusal_code=refusal.refusal_code.value,
            domain=domain
        )

        return (False, refusal)

    return (True, None)
```

**Drift Monitor (after):**
```python
from constitutional_memory.memory import record_drift

def check_freeze_violations(self):
    violations = self._detect_modifications()

    if violations:
        # Record drift detection
        record_drift(
            self.memory,
            drift_type="freeze_violation",
            severity="critical",
            details=f"Modified: {violations}"
        )

    return violations
```

---

## Hash Chain (Tamper Evidence)

Each event includes:
- `previous_hash`: Hash of previous event (or "0000...0000" for genesis)
- `event_hash`: SHA256 of (sequence + timestamp + type + data + previous_hash)

Same pattern as VSD audit logs. Chain integrity verifiable via `cli.py verify`.

---

## Access Rules

- **Read:** Any component can read history (observation)
- **Write:** Append-only (no modification, no deletion)
- **Authority:** None (memory makes zero decisions)

---

## What This Enables

**Session continuity:** Nova observes its own constitutional history across time

**Pattern detection:** Repeated boundary probes visible (e.g., same F-domain hit 10 times)

**Reduced operator burden:** Context available without manual re-injection

**Audit trail:** Constitutional events tamper-evident and reproducible

**What it does NOT enable:**
- Nova learning or adapting
- Automatic boundary changes
- Authority expansion
- Decision automation

---

## Deletion Policy

If constitutional memory proves unnecessary → delete this directory.

If it proves useful → it survives.

Evolutionary pressure, not architectural destiny.

---

## Version

v0.1 - Minimal viable implementation
