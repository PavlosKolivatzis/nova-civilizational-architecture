# Developer Guide

This guide provides a quick reference for setting up the NOVA development environment, running tests, and understanding how the system's slots interact.

## Setup

1. **Create and activate a virtual environment** (optional but recommended).
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the orchestrator** or individual modules as needed for development.

## Testing

The project uses `pytest` for automated tests. From the repository root, run:

```bash
pytest
```

This will execute all tests in the `tests/` directory.

## Slot Interactions

NOVA's architecture revolves around an **Orchestrator** and a **Slot Loader** that manage a collection of specialized slots. Each slot provides focused capabilities (truth anchoring, cultural synthesis, distortion protection, etc.) and communicates through defined contracts. The test framework and WebSocket interface interact with the orchestrator and loader as shown below.

![Slot relationships](slot_relationships.svg)

When adding a new slot, implement the required contract in the `src/nova/slots/` directory and ensure the slot loader can discover it. The orchestrator will then route interactions through the new slot alongside existing ones.
