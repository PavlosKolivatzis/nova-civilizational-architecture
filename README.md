# NOVA Civilizational Architecture

## 🎯 Overview
Production-grade multicultural truth synthesis engine with 10-slot cognitive architecture for civilizational-scale deployment.

## 🔧 Status: Private Development
- ✅ **Slot 6 Adaptive Synthesis Engine v7.4.1** - Ready for integration
- ✅ **Slot 10 Integration Patches** - Surgical precision updates  
- ✅ **Complete Testing Framework** - Validation ready
- ✅ **Production Deployment Bundle** - API + Dashboard

## 📋 Quick Start
1. See `integration_guide.md` for deployment instructions
2. Review `Slot6_enhancement.md` for technical details
3. Apply patches from `Slot10_patches.md`
4. Run tests from `testing_framework.md`

## 📦 Dependencies

Key dependencies are pinned for reproducible installs:

- PyYAML 6.0.2
- typing-extensions 4.14.1
- pytest-asyncio 1.1.0

## 🛡️ Architecture
10-slot cognitive framework:
- **Slots 1-5:** Core truth processing
- **Slot 6:** Cultural adaptation (Adaptive Synthesis Engine v7.4.1)
- **Slots 7-10:** Production deployment

## 🔒 Repository Status
**Private** - Strategic development phase

## ⚙️ Orchestrator & Slot-10 Deployment

The asynchronous `NovaOrchestrator` wraps Slot 6 cultural guardrails and
optionally enables Slot 10 node deployment. Enable it via feature flags:

- `NOVA_SLOT10_ENABLED` – activate Slot 10 deployer (default `false`)
- `NOVA_GM_ENABLED` – turn on geometric-memory caching (default `false`)
- `NOVA_LOG_LEVEL` – logging verbosity (default `INFO`)

Usage:

```bash
export NOVA_SLOT10_ENABLED=true
python app.py --deploy "MIT_AI_Lab" --type academic
```

The system degrades gracefully if optional modules like TRI or ΔTHRESH
are absent.
