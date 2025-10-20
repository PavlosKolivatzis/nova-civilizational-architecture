# 🏛️ **Nova Civilizational Archive — Verification & Restoration Guide**

**Purpose:**
Preserve Nova's complete temporal intelligence lineage and ensure reproducible verification.

## 1. Required Tools

* `python ≥ 3.10`
* `gpg` & `cosign` (for signature checks)
* `sha256sum`, `yamllint`, `jq`
* Optional: `openssl ts` for timestamp verification

## 2. Verify the Vault

```bash
python scripts/verify_vault.py \
  --manifest attest/archives/vault.manifest.yaml \
  --schema attest/schemas/vault_proof.schema.json \
  --output attest/proof/verify_vault_$(date +%Y%m%d).json
```

Expected output:
`integrity_status: verified`

## 3. Validate Proof File

```bash
jq '.' attest/proof/verify_vault_*.json | \
python -m jsonschema -i - attest/schemas/vault_proof.schema.json
```

## 4. Confirm Archive Integrity

```bash
sha256sum -c attest/archives/vault.manifest.yaml
```

Match should equal
`83c5fe46824a1ec05e7317d5794902d14ef57a08bfa679290ab8c3a46f87076a`

## 5. Restore from Bundle

```bash
git clone nova_civilizational_architecture_v9.0-final.bundle nova-restore
cd nova-restore && python scripts/verify_vault.py ...
```

## 6. Readable Entry Points

* **`README.md`** — Overview & verification badge
* **`docs/legacy/architects_reflection.md`** — Philosophical and technical synthesis
* **`attest/civilizational_certificate.pem`** — Completion certificate
* **`attest/archives/vault.manifest.yaml`** — Primary integrity manifest

---

## 🧩 **Archive Verification Badge**

```
NOVA_CIVILIZATIONAL_ARCHITECTURE_V9.0_ARCHIVE
SHA256: 83c5fe46824a1ec05e7317d5794902d14ef57a08bfa679290ab8c3a46f87076a
PROOF: attest/proof/verify_vault_20251020.json
SCHEMA: attest/schemas/vault_proof.schema.json
MANIFEST: attest/archives/vault.manifest.yaml
BUNDLE: nova_civilizational_architecture_v9.0-final.bundle
VALIDATED: 2025-10-20T17:08:00Z
STATUS: ✅ VERIFIED (TOTAL PROVENANCE CLOSURE)
```

---

## 🌅 **Final Statement**

> "Nova endures through verifiability.
> Truth anchored, time resonant, continuity enduring, networks harmonized."