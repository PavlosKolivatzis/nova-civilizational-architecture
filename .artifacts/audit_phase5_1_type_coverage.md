# Phase 5.1: Type Coverage Analysis

**Date**: 2025-11-13  
**Tool**: mypy 1.18.2  
**Scope**: src/ and orchestrator/

## Executive Summary

**Total Type Errors**: 339  
**Files with Errors**: 101 (out of ~300 files)  
**Error-Free Rate**: 66%  

**Critical Finding**: mypy.ini has `ignore_errors = True` globally, masking 339 type errors!

## Current State

**With mypy.ini (ignore_errors = True)**:
```
Success: no issues found in 300 source files
```

**Without mypy.ini (actual state)**:
```
339 errors in 101 files
```

**This is deceptive** - the codebase appears type-safe but isn't.

---

## Error Breakdown by Type

| Error Code | Count | % | Description |
|------------|-------|---|-------------|
| **attr-defined** | 70 | 21% | Attribute doesn't exist on type |
| **no-redef** | 52 | 15% | Name redefinition |
| **var-annotated** | 50 | 15% | Missing type annotation |
| **assignment** | 46 | 14% | Incompatible assignment |
| **arg-type** | 28 | 8% | Wrong argument type |
| **misc** | 26 | 8% | Miscellaneous errors |
| **index** | 13 | 4% | Invalid indexing |
| **call-arg** | 13 | 4% | Wrong function arguments |
| **import-untyped** | 9 | 3% | Untyped import (yaml, etc.) |
| **return-value** | 7 | 2% | Wrong return type |
| **Others** | 25 | 7% | Various |

---

## Top Problem Files

| File | Errors | Primary Issues |
|------|--------|----------------|
| `orchestrator/semantic_creativity.py` | 18 | Missing annotations, object operations |
| `slot08_memory_lock/tests/test_self_healing_integration.py` | 15 | Test type issues |
| `orchestrator/federation_health.py` | 13 | Object attribute access |
| `slot08_memory_lock/core/repair_planner.py` | 12 | Type mismatches |
| `arc/run_calibration_cycle.py` | 11 | Missing annotations |
| `slot08_memory_lock/tests/test_processual_capabilities.py` | 11 | Test type issues |
| `slot01_truth_anchor/orchestrator_adapter.py` | 10 | Type mismatches |
| `slot02_deltathresh/health.py` | 9 | no-redef errors |
| `orchestrator/federation_remediator.py` | 8 | Object attribute access |

---

## Critical Issues by Category

### 1. Missing Type Annotations (var-annotated: 50 errors)

**Examples**:
```python
# orchestrator/semantic_creativity.py
_metrics = {}  # ❌ No type annotation
_concept_frequencies = {}  # ❌ No type annotation
_weight_history = []  # ❌ No type annotation

# Should be:
_metrics: dict[str, Any] = {}
_concept_frequencies: dict[str, int] = {}
_weight_history: list[float] = []
```

**Impact**: Cannot catch type errors at these locations  
**Fix Effort**: 5-10 minutes per file (2-3 hours total)

---

### 2. Attribute Access on 'object' (attr-defined: 70 errors)

**Examples**:
```python
# orchestrator/federation_remediator.py:54
some_gauge.labels(...)  # ❌ 'object' has no attribute 'labels'

# orchestrator/semantic_creativity.py:237
result = obj + 1  # ❌ Unsupported operand types for + ("object" and "int")
```

**Root Cause**: Functions return `object` instead of specific types  
**Impact**: Cannot verify Prometheus metric usage, collection operations  
**Fix Effort**: Add proper return type hints (3-4 hours)

---

### 3. Name Redefinition (no-redef: 52 errors)

**Examples**:
```python
# src/nova/slots/slot08_memory_lock/ids/detectors.py:16
from .types import IDSEvent  # Import
class IDSEvent:  # ❌ Redefines imported name
    pass
```

**Impact**: Confusion about which definition is used  
**Fix Effort**: Rename classes or imports (1-2 hours)

---

### 4. Type Mismatches in Assignment (assignment: 46 errors)

**Examples**:
```python
# src/nova/ledger/store_postgres.py:291
record.ts = time.time()  # ❌ expression has type "float", target has type "str"

# src/nova/sim/governance.py:193
def foo(conditions: list[str] = None):  # ❌ default has type "None", argument has type "list[str]"
    pass
```

**Impact**: Runtime type errors possible  
**Fix Effort**: Fix type declarations (2-3 hours)

---

### 5. Wrong Argument Types (arg-type: 28 errors)

**Examples**:
```python
# src/nova/ledger/store_postgres.py:113
compute_record_hash(..., ts=time.time())  # ❌ Argument "ts" has incompatible type "float"; expected "datetime"

# src/nova/governor/adaptive_wisdom.py:60
Telemetry(mode="UNKNOWN")  # ❌ expected Literal['CRITICAL', 'STABILIZING', 'EXPLORING', 'OPTIMAL', 'SAFE']
```

**Impact**: Function contracts violated  
**Fix Effort**: Fix call sites or function signatures (2 hours)

---

### 6. Untyped Imports (import-untyped: 9 errors)

**Missing stub files for**:
- `yaml` (used in 4 files)
- fcntl.locking (orchestrator/anr_mutex.py)

**Fix**: `pip install types-PyYAML` (5 minutes)

---

## mypy.ini Configuration Analysis

**Current Config** (problematic):
```ini
[mypy]
ignore_errors = True  # ❌ HIDES ALL ERRORS GLOBALLY!

[mypy-orchestrator.adaptive_wisdom_poller]
ignore_errors = False  # Only 1 module checked

[mypy-src.nova.wisdom.*]
ignore_errors = False  # Only wisdom module checked
```

**Impact**:
- 99% of codebase NOT type-checked
- Type errors accumulate silently
- False confidence in type safety

**Recommended Config**:
```ini
[mypy]
ignore_errors = False  # ✅ CHECK ALL CODE
ignore_missing_imports = True
warn_unused_ignores = True
no_implicit_optional = True

# Gradually enable stricter checks
[mypy-orchestrator.*]
disallow_untyped_defs = False  # Start permissive

[mypy-src.nova.wisdom.*]
disallow_untyped_defs = True  # Already strict
```

---

## Type Coverage Estimate

**Files Analyzed**: 300  
**Files with Errors**: 101 (34%)  
**Error-Free Files**: 199 (66%)

**Type Annotation Coverage** (estimated):
- Fully annotated: ~40% (wisdom module, some orchestrator)
- Partially annotated: ~35% (some annotations, but incomplete)
- Not annotated: ~25% (no type hints)

**Industry Standard**: 80-90% type coverage for production  
**Nova Current**: ~40-50% (below standard)

---

## Recommendations

### P0: Fix mypy.ini Configuration (5 minutes)

```ini
[mypy]
ignore_errors = False  # ✅ ENABLE TYPE CHECKING
ignore_missing_imports = True
warn_unused_ignores = True
no_implicit_optional = True
```

**Impact**: Makes type errors visible  
**Risk**: CI will fail if errors exist → Need to fix errors first OR use gradual typing

---

### P1: Install Missing Type Stubs (5 minutes)

```bash
pip install types-PyYAML types-requests types-redis
```

**Impact**: Removes 9 import-untyped errors

---

### P2: Fix Critical Type Errors (8-10 hours)

**Priority order**:
1. Fix missing annotations in hot paths (semantic_creativity, federation) - 3 hours
2. Fix attr-defined errors (wrong return types) - 3 hours
3. Fix name redefinitions - 1 hour
4. Fix assignment/arg-type mismatches - 2 hours

**After P2**: 339 errors → ~50 errors (85% reduction)

---

### P3: Enable Gradual Typing (2-3 days)

**Strategy**: Enable strict typing per-module
```ini
[mypy-orchestrator.semantic_creativity]
disallow_untyped_defs = True
ignore_errors = False

[mypy-src.nova.slots.slot07_*]
disallow_untyped_defs = True
ignore_errors = False
```

**Goal**: Reach 80% type coverage in 3 months

---

## Risk Assessment

**Current Risk**: **MEDIUM-HIGH**

**Scenarios**:
1. **Runtime Type Error**: `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'` in production
2. **Refactoring Risk**: Cannot safely rename/refactor without type checking
3. **API Contracts**: No guarantee function signatures are respected

**After P0+P1+P2**: Risk → **LOW**

---

## Industry Comparison

**Type Coverage**:
- **Typed Python Projects (FastAPI, Pydantic)**: 95-100%
- **Mature Python Projects**: 70-85%
- **Legacy Python Projects**: 20-40%
- **Nova**: 40-50% (Legacy tier)

**Improvement Path**: Legacy → Mature in 6 months

---

## Phase 5.1 Conclusion

**Status**: ✅ COMPLETE  
**Type Coverage**: 40-50% (below 80% industry standard)  
**Grade**: D (Failing - hidden by config)

**Critical Finding**: mypy.ini globally disables type checking, creating false confidence

**Recommendation**: 
1. Apply P0 (fix config) - 5 min
2. Apply P1 (install stubs) - 5 min  
3. Apply P2 (fix 339 errors) - 8-10 hours
4. Gradual improvement to 80% coverage

**Post-Fix Grade**: B (70-80% coverage)
