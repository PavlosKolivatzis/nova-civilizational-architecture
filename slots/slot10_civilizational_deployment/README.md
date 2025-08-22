# Slot 10: Civilizational Deployment

Lightweight deployment layer wrapping Slot 6 cultural guardrails.

## Modules

- `models.py` – deployment enums and result dataclasses
- `mls.py` – MetaLegitimacySeal final validator
- `phase_space.py` – NovaPhaseSpaceSimulator topology snapshot
- `deployer.py` – InstitutionalNodeDeployer pipeline

## Event Flow

- `content.validate` → `content.approved` / `content.blocked`
- `deploy.node` → register node via Slot 10
- `system.status` → uptime and slot availability

Enable via `NOVA_SLOT10_ENABLED=true`. Optional caches and TRI/ΔTHRESH
are used when present; missing components degrade gracefully.
