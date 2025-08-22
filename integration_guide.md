## **File 3: integration_guide.md**

```markdown
# NOVA Enhancement - Integration Guide

## Quick Start Checklist

### Step 1: Create New Slot 6 File
- [ ] Create `slot06_cultural_synthesis/multicultural_truth_synthesis.py`
- [ ] Copy entire code from `slot6_enhancement.md`
- [ ] Save file

### Step 2: Apply Slot 10 Patches
- [ ] Open your Slot 10 files in Acode
- [ ] Apply Patch 1: MetaLegitimacySeal (1 method replacement)
- [ ] Apply Patch 2: InstitutionalNodeDeployer (4 additions)
- [ ] Apply Patch 3: CivilizationalOrchestrator (5 changes)

### Step 3: Update Imports
Add to your Slot 10 file that uses Slot 6:

```python
from slot06_cultural_synthesis.multicultural_truth_synthesis import MulticulturalTruthSynthesis
```

### Step 4: Test Integration
Run your existing NOVA demo to verify everything works.

## Detailed Workflow

### Using Acode for Patches
- Open your Slot 10 files in Acode
- Use `Ctrl+F` to search for the exact strings in `slot10_patches.md`
- Select and replace the specified code sections
- Save each file after applying patches

### Search Tips in Acode
- Use `Ctrl+F` to open search
- Search for method signatures like `def _screen_with_slot2`
- Use Find & Replace for simple text substitutions
- Save frequently to avoid losing changes

## Verification Steps
After applying all patches:
- Check imports - no missing modules
- Run syntax check - no Python errors
- Test basic functionality - existing demos still work
- Verify new features - rate limiting, diversity metrics

## Troubleshooting

### Common Issues
- **Import Errors:** Ensure `slot06_cultural_synthesis/multicultural_truth_synthesis.py` is in correct location and all import statements are properly added.
- **Method Not Found:** Verify you replaced entire methods, not just parts, and check indentation matches existing code style.
- **Rate Limiting Issues:** Ensure `from collections import deque` is added and `self._deploy_ts = deque(maxlen=256)` is in `__init__`.

## Testing Commands

```bash
python -m py_compile nova/slot6_multicultural_truth_synthesis.py

# Run existing demos
python your_slot10_demo.py

# Test new Slot 6 directly
python -c "from slot06_cultural_synthesis.multicultural_truth_synthesis import MulticulturalTruthSynthesis; print('Import successful')"
```

## Success Indicators
You'll know integration worked when:
- [ ] No import errors when loading Slot 6
- [ ] Existing Slot 10 demos run without errors
- [ ] New cultural metrics appear in output
- [ ] Rate limiting prevents excessive deployments
- [ ] Health monitoring shows as cancellable

## Performance Expectations
After integration:
- Cultural profiling: Quantified adaptation scores instead of labels
- Deployment success: Higher approval rates via transformation
- Safety: Forbidden element blocking active
- Monitoring: Real-time cultural diversity tracking

Ready to deploy! 🚀
