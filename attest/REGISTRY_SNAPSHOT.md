# 🗂 Nova Epoch v10 — Registry Snapshot

**Generated:** 2025-10-21
**Epoch:** Phase 10.0 – Ethical Autonomy & Federated Cognition
**Status:** Sealed & Verified

---

## Artifact Registry

| Artifact | Path | Purpose | SHA-256 Checksum |
|----------|------|---------|------------------|
| **Phase 10 Attestation** | `attest/phase10_complete.yaml` | Canonical cryptographic proof of completion | `83edb26838e5a1a9970c891d0e2bfa60b25a9bbe` (commit hash) |
| **Manifest** | `attest/manifests/phase10_manifest.json` | Portable machine-readable verification record | `c5635942f48dc6265b7c9cda8f65e11bbb07084e62bb06d806ca8a08860fd340` |
| **Archive** | `../nova_epoch_v10_archive.tgz` | Cold-storage bare Git mirror (33 MB) | `6f947c13adb3b15815d3cb45eebd783bef21aa4d610750dadc05d5367b8f68cc` |
| **Archive Checksum** | `../nova_epoch_v10_archive.sha256` | Archive integrity verification | (file contains archive SHA-256) |
| **Epoch Manifest** | `EPOCH_V10_MANIFEST.md` | Human-readable restoration guide | `58ac12a` (commit) |

---

## Verification Procedures

### 1. Verify Archive Integrity
```bash
cd ..
sha256sum -c nova_epoch_v10_archive.sha256
# Expected: nova_epoch_v10_archive.tgz: OK
```

### 2. Verify Manifest Integrity
```bash
cd attest/manifests
sha256sum -c phase10_manifest.sha256
# Expected: phase10_manifest.json: OK
```

### 3. Verify Git Lineage
```bash
git log --oneline --graph --decorate \
  v6.0-belief-propagation..v10.0-complete
```

### 4. Verify Test Suite
```bash
git checkout v10.0-complete
python -m pytest tests/ -q
# Expected: 1074 passed
```

---

## Manifest Contents

**File:** `attest/manifests/phase10_manifest.json`

Key fields:
- `epoch`: "10.0"
- `git.commit`: "83edb26838e5a1a9970c891d0e2bfa60b25a9bbe"
- `git.branch`: "epoch-v10"
- `validation.tri_score`: 0.81
- `validation.resilience_class`: "B"
- `tests.total`: 1074
- `tests.passing`: 1074
- `modules`: FEP, PCR, AG, CIG, FLE-II

---

## Distribution Channels

### Primary (Git)
- **Branch:** `epoch-v10` (frozen, protected)
- **Tag:** `v10.0-complete` (annotated)
- **Remote:** `https://github.com/PavlosKolivatzis/nova-civilizational-architecture.git`

### Archive (Local)
- **Location:** `../nova_epoch_v10_archive.tgz`
- **Size:** 33 MB (compressed)
- **Format:** Git bare repository (tar.gz)

### IPFS (Optional)
IPFS pinning not performed (daemon not installed).

To pin manifest to IPFS:
```bash
ipfs add -Q attest/manifests/phase10_manifest.json
# Returns: QmXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## Restoration Scenarios

### Scenario 1: Full Clone from GitHub
```bash
git clone -b epoch-v10 \
  https://github.com/PavlosKolivatzis/nova-civilizational-architecture.git
cd nova-civilizational-architecture
git checkout v10.0-complete
```

### Scenario 2: Restore from Archive
```bash
tar -xzf nova_epoch_v10_archive.tgz
git clone nova_epoch_v10.git nova-restored
cd nova-restored
git checkout epoch-v10
```

### Scenario 3: Verify Specific Commit
```bash
git checkout 83edb26838e5a1a9970c891d0e2bfa60b25a9bbe
python -m pytest tests/ -q
npm run maturity
```

---

## Governance Notes

1. **Branch Protection:** Recommended to lock `epoch-v10` on GitHub (Settings → Branches → Add rule)
2. **Archive Storage:** Recommended to store archive + checksums in at least 3 geographically distributed locations
3. **Ethics Review:** `attest/phase10_complete.yaml` should be submitted to ethics board for quarterly audit
4. **Monitoring:** If deployed to production, enable Prometheus scraping of `/metrics` endpoint
5. **Rollback:** To revert Phase 10, use `git reset --hard dbbd385` (Phase 9 complete)

---

## External Verification

Third parties can verify Nova Epoch v10 integrity using:

1. **Manifest:** Download `phase10_manifest.json` and verify SHA-256
2. **Git Tag:** Clone repository and verify tag signature (if GPG-signed)
3. **Tests:** Run full test suite and compare against manifest (`tests.total: 1074`)
4. **Archive:** Request archive + checksum file, verify SHA-256 matches manifest

---

**Registry Snapshot Status:** ✅ Complete
**Next Action:** Protect branch, archive storage, ethics review
