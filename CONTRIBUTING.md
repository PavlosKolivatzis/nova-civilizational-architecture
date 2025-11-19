# Contributing to Nova Civilizational Architecture

## Development Guidelines

### Phase 6.x Integration Rule
All probabilistic or uncertainty-aware components must register their belief metrics under `nova_slot_phase_lock_belief_*` and follow `contracts/slot04-07-belief-state.yaml`. No slot-to-slot propagation outside this schema is permitted.

### Code Standards
- Follow PEP 8 with 120-character line limits
- Use type hints for all public APIs
- Include comprehensive docstrings
- Write tests for all new functionality

### Testing Requirements
- All tests must pass: `pytest -q`
- Code must pass linting: `ruff check src/nova orchestrator tests`
- Type checking must pass: `mypy src/nova orchestrator scripts`
- Contract interfaces must stay in sync: `python scripts/contract_audit.py`

### Commit Conventions
Follow Conventional Commits format: `type(scope): subject`
- Types: feat, fix, docs, style, refactor, test, chore
- Scope: slot name or component (e.g., slot04, orchestrator)
- Subject: lowercase, ≤72 characters

### Pull Request Process
1. Create feature branch from main
2. Implement changes with tests
3. Update documentation as needed
4. Ensure CI passes
5. Request review with clear description
6. Merge after approval

## Architecture Principles

### Slot-Based Design
- Each slot is independently deployable
- Clear contracts between slots
- Graceful degradation on failures

### Observability First
- All components emit structured metrics
- Comprehensive logging with correlation IDs
- Health endpoints for all services

### Security by Design
- Input validation on all boundaries
- Rate limiting and circuit breakers
- Audit logging for sensitive operations

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `pytest`
4. Check code quality: `ruff check src/nova orchestrator tests`

## Release Process

See `docs/releases/` for detailed release procedures and phase management.
