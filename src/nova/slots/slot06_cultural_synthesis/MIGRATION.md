# Slot 6 Cultural Synthesis Migration Guide

## Overview

Slot 6 has been refactored from a monolithic `multicultural_truth_synthesis.py` to a clean modular architecture:
- `engine.CulturalSynthesisEngine` - Core synthesis logic
- `adapter.CulturalSynthesisAdapter` - Integration adapter

The legacy `multicultural_truth_synthesis` module is maintained for backward compatibility but is deprecated.

## Migration Path

### Current API (Recommended)

```python
from nova.slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine
from nova.slots.slot06_cultural_synthesis.adapter import CulturalSynthesisAdapter

engine = CulturalSynthesisEngine()
adapter = CulturalSynthesisAdapter(engine)

# Direct synthesis
profile = {"institution": "TestInst", "region": "EU", "tri_score": 0.8}
result = engine.synthesize(profile)  # Returns Dict[str, Any]

# Via adapter
cultural_profile = adapter.analyze_cultural_context("TestInst", {"region": "EU"})
```

### Legacy API (Deprecated)

```python
# ⚠️ DEPRECATED - Issues DeprecationWarning
from nova.slots.slot06_cultural_synthesis.multicultural_truth_synthesis import (
    AdaptiveSynthesisEngine,
    MulticulturalTruthSynthesisAdapter
)

engine = MulticulturalTruthSynthesisAdapter(AdaptiveSynthesisEngine())
profile = engine.analyze_cultural_context("TestInst", {"region": "EU"})
# Returns ProfileWrapper with both dict[key] and obj.attr access
```

## Deprecation Timeline

### Phase 1: Current (Warnings + Metrics)
- **Status**: Active warnings and usage tracking
- **Timeline**: Current release
- **Actions**:
  - Legacy module issues `DeprecationWarning` on import
  - Usage tracked via `get_legacy_usage_count()`
  - Health endpoint exposes legacy metrics at `/health/config`
  - CI tests both new and legacy APIs

### Phase 2: Environment Gate (Next Release)
- **Status**: Planned
- **Timeline**: Next minor release
- **Actions**:
  - Default CI job blocks legacy with `NOVA_BLOCK_LEGACY_SLOT6=1`
  - Legacy compatibility job maintains regression testing
  - Documentation updates emphasize new API
  - Breaking change warnings in release notes

### Phase 3: Removal (+1 Release)
- **Status**: Planned
- **Timeline**: Following minor release
- **Actions**:
  - Remove `multicultural_truth_synthesis.py` entirely
  - Remove legacy compatibility tests
  - Clean CI to use only new API
  - Archive migration documentation

## Key Differences

### Return Types
- **Legacy**: Returns `ProfileWrapper` with both `obj.attr` and `obj['key']` access
- **New**: Returns standard `Dict[str, Any]` (CulturalProfile)

### Interface
- **Legacy**: `analyze_cultural_context(institution, context)`
- **New**: `synthesize(profile)` where profile includes institution

### Error Handling
- **Legacy**: Returns safe defaults on exceptions
- **New**: Propagates exceptions for explicit handling

## Contract Stability

The `CULTURAL_PROFILE@1` contract is stable across both APIs:

Required keys:
- `principle_preservation_score` (0.0-1.0)
- `residual_risk` (0.0-1.0)
- `policy_actions` (List)
- `forbidden_hits` (List)
- `consent_required` (bool)

## Testing

Schema contract tests ensure API stability:
```bash
pytest tests/contracts/test_cultural_profile_schema.py
```

Legacy compatibility tests:
```bash
pytest tests/test_slot06_legacy_compatibility.py
```

## Observability

Monitor legacy usage via health endpoint:
```bash
curl /health/config
```

Look for `slot6.legacy_calls_total` metric to track adoption.

## Support

For migration questions or issues, reference:
- Schema contract tests for expected behavior
- Legacy compatibility tests for transition patterns
- Health metrics for usage tracking
