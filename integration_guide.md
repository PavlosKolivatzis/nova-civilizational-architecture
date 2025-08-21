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
from slot06_cultural_synthesis.multicultural_truth_synthesis import MulticulturalTruthSynthesisStep 4: Test IntegrationRun your existing NOVA demo to verify everything works.Detailed WorkflowUsing Acode for PatchesOpen your Slot 10 files in AcodeUse Ctrl+F to search for the exact strings in slot10_patches.mdSelect and replace the specified code sectionsSave each file after applying patchesSearch Tips in AcodeUse Ctrl+F to open searchSearch for method signatures like def _screen_with_slot2(Use Find & Replace for simple text substitutionsSave frequently to avoid losing changesVerification StepsAfter applying all patches:Check imports - no missing modulesRun syntax check - no Python errorsTest basic functionality - existing demos still workVerify new features - rate limiting, diversity metricsTroubleshootingCommon IssuesImport Errors:Ensure slot06_cultural_synthesis/multicultural_truth_synthesis.py is in correct locationCheck all import statements are properly addedMethod Not Found:Verify you replaced entire methods, not just partsCheck indentation matches existing code styleRate Limiting Issues:Ensure from collections import deque is addedVerify self._deploy_ts = deque(maxlen=256) is in __init__Testing Commands# Basic syntax check
python -m py_compile nova/slot6_multicultural_truth_synthesis.py

# Run existing demos
python your_slot10_demo.py

# Test new Slot 6 directly
python -c "from slot06_cultural_synthesis.multicultural_truth_synthesis import MulticulturalTruthSynthesis; print('Import successful')"Success IndicatorsYou'll know integration worked when:[ ] No import errors when loading Slot 6[ ] Existing Slot 10 demos run without errors[ ] New cultural metrics appear in output[ ] Rate limiting prevents excessive deployments[ ] Health monitoring shows as cancellablePerformance ExpectationsAfter integration:Cultural profiling: Quantified adaptation scores instead of labelsDeployment success: Higher approval rates via transformationSafety: Forbidden element blocking activeMonitoring: Real-time cultural diversity trackingReady to deploy! 🚀---
