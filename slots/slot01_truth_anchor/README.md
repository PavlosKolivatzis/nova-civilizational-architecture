# Slot 1: Truth Anchor & Recovery System

## Status: Operational ✅
Core reality lock with recovery protocols.

## Components:
- Truth anchor crystallization
- Cryptographic RealityLock structure
- Emergency stabilization systems
- Recovery protocol frameworks

## Integration Points:
- Provides foundation for all other slots
- Recovery system for system failures
- Truth verification backbone

## Key Management
- `TruthAnchorEngine` accepts an optional `secret_key` during initialization.
- When omitted, a new 32-byte key is generated automatically.
- Use `export_secret_key()` to retrieve the key and store it securely for reuse.

## Logging
- `TruthAnchorEngine` does not configure logging handlers internally.
- Configure logging via application settings or pass a custom `Logger` instance
  to the constructor.

## Cryptographic RealityLock
Anchors are secured by a `RealityLock` pairing each anchor string with a
SHA-256 integrity hash. Create one with
`RealityLock.from_anchor("anchor_id")` and validate it via
`verify_integrity()`. The `RealityVerifier` offers thread-safe
verification and metrics without holding the lock during hashing.

## Cache Usage
Slot discovery uses an in-memory file index cache. Entries are refreshed
on demand and can be rebuilt with
`slot_loader.find_file(base_dir, refresh=True)`. For geometric-memory
caching, enable the `NOVA_GM_ENABLED` environment variable. Cached items
honor their time-to-live and are ignored when caching is disabled.

## Public API & Migration Notes
`TruthAnchorEngine` v1.2 introduces `export_secret_key()` for key
rotation. The previous `Lock` class is now `RealityLock`; `Lock` remains
as an alias, but new code should import `RealityLock` and, when needed,
use the accompanying `RealityVerifier`.
