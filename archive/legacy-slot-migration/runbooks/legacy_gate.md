⚠️ Legacy Context: This document reflects the pre-namespaced `slots/slotXX_*` layout. Active code now lives under `src/nova/slots/slotXX_*`. See `README.md#directory-legend` for mapping.

# Runbook: Legacy Gate Remediation

## Problem
Legacy Slot 6 API is blocked by `NOVA_BLOCK_LEGACY_SLOT6=1` but application still trying to use deprecated imports.

## Symptoms
- `ImportError: Legacy Slot6 API is disabled`
- CI failures in legacy compatibility tests
- Application startup failures with legacy import errors
- `/health/config` shows `legacy_calls_total: null`

## Investigation Steps

### 1. Identify Legacy Usage
```bash
# Check for legacy imports in codebase
grep -r "multicultural_truth_synthesis" . --include="*.py"
grep -r "AdaptiveSynthesisEngine" . --include="*.py"
grep -r "MulticulturalTruthSynthesisAdapter" . --include="*.py"
```

### 2. Check Environment Configuration  
```bash
# Verify environment gate is active
echo $NOVA_BLOCK_LEGACY_SLOT6

# Check CI matrix configuration
cat .github/workflows/nova-ci.yml | grep -A5 -B5 "NOVA_BLOCK_LEGACY_SLOT6"
```

### 3. Examine Failed Import Stack Traces
```bash
# Get full stack trace of import failure
python -c "
try:
    from nova.slots.slot06_cultural_synthesis.multicultural_truth_synthesis import AdaptiveSynthesisEngine
    print('Legacy import succeeded (unexpected)')
except ImportError as e:
    print(f'Legacy import blocked: {e}')
"
```

## Resolution Options

### Option 1: Migrate to New API (Recommended)
Replace legacy imports with new API:

```python
# OLD (blocked):
from nova.slots.slot06_cultural_synthesis.multicultural_truth_synthesis import (
    AdaptiveSynthesisEngine,
    MulticulturalTruthSynthesisAdapter
)
engine = MulticulturalTruthSynthesisAdapter(AdaptiveSynthesisEngine())
profile = engine.analyze_cultural_context('Institution', {'region': 'EU'})

# NEW (supported):
from nova.slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine
from nova.slots.slot06_cultural_synthesis.adapter import CulturalSynthesisAdapter

engine = CulturalSynthesisEngine()
adapter = CulturalSynthesisAdapter(engine)
profile = adapter.analyze_cultural_context('Institution', {'region': 'EU'})
```

### Option 2: Temporary Legacy Re-enable (Emergency Only)
```bash
# For critical hotfixes only - requires engineering approval
export NOVA_BLOCK_LEGACY_SLOT6=0

# Or update CI job to use legacy-compat matrix
# Edit .github/workflows/nova-ci.yml:
# Use 'legacy-compat' job instead of 'standard-blocked'
```

### Option 3: Skip Legacy Tests
If tests are failing, verify they're properly skipped:
```python
# Ensure tests have proper skip decoration:
import pytest
import os

def _env_truthy(name: str) -> bool:
    v = os.getenv(name, "")
    return v.lower() in {"1", "true", "yes", "on"}

pytestmark = pytest.mark.skipif(
    _env_truthy("NOVA_BLOCK_LEGACY_SLOT6"),
    reason="Legacy Slot6 API blocked by NOVA_BLOCK_LEGACY_SLOT6"
)
```

## Migration Checklist

- [ ] Identify all legacy import locations
- [ ] Update imports to new API pattern
- [ ] Test new API compatibility 
- [ ] Verify contract compliance (CULTURAL_PROFILE@1)
- [ ] Update documentation references
- [ ] Remove legacy test dependencies
- [ ] Validate CI pipeline passes

## API Migration Reference

| Legacy Pattern | New Pattern |
|----------------|-------------|
| `AdaptiveSynthesisEngine()` | `CulturalSynthesisEngine()` |
| `MulticulturalTruthSynthesisAdapter(engine)` | `CulturalSynthesisAdapter(engine)` |
| `engine.analyze_cultural_context()` | `adapter.analyze_cultural_context()` |
| `profile.adaptation_effectiveness` | `profile["adaptation_effectiveness"]` |
| `ProfileWrapper` access | Standard `dict` access |

## Prevention

1. **Code scanning**: Add pre-commit hooks to detect legacy imports
2. **Documentation**: Update all examples to use new API
3. **Training**: Ensure team knows migration path
4. **Monitoring**: Track legacy usage via health endpoint

## Timeline

- **Current**: Legacy blocked by default in CI, warnings in development
- **Next release**: Legacy module deprecated with clear migration timeline  
- **Following release**: Legacy module removed entirely

## Escalation

Contact `#nova-architecture` for guidance on complex migration scenarios.