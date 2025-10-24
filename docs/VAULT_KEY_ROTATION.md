# Vault Signing Key Rotation Guide

Nova’s continuity audit relies on two signing mechanisms:

- **cosign** for the `.sig` signature over `attest/archives/vault.manifest.yaml`
- **GPG** for the detached ASCII-armored signature `vault.manifest.yaml.asc`

This guide documents how to regenerate both key pairs in an automated, reproducible way so an operator—or an autonomous agent—can bootstrap a fresh environment without human prompts.

## 1. Prerequisites

- Python 3.10+ (for running helper scripts)
- Git for Windows (provides `sha256sum.exe`)
- `cosign` will be downloaded automatically via `scripts/bootstrap_audit_tools.py`
- `gpg` installed and available on `PATH`

Before rotating keys:

```bash
python scripts/bootstrap_audit_tools.py
```

This downloads/validates `cosign.exe` and writes `tools/audit/paths.env` with tool locations.

## 2. Cosign Key Pair

Cosign keys are stored outside the repository in `%USERPROFILE%\.nova\trust` to keep the private key out of version control.

### Generate a new key pair

```cmd
rem Choose a passphrase (can be empty for local ops). Environment will prompt if omitted.
set COSIGN_PASSWORD=password123
.\\tools\\audit\\cosign.exe generate-key-pair --output-key-prefix %USERPROFILE%\\.nova\\trust\\cosign
```

### Export public key to the repo

```powershell
Copy-Item "$env:USERPROFILE\.nova\trust\cosign.pub" trust\cosign.pub -Force
```

### (Optional) Rotate passphrase

```cmd
set COSIGN_PASSWORD=newpass
.\\tools\\audit\\cosign.exe password --key %USERPROFILE%\\.nova\\trust\\cosign.key
```

## 3. GPG Key Pair

The vault manifest expects the signer `Nova Ops Audit <ops-audit@example.com>` with fingerprint recorded in `attest/archives/vault.manifest.yaml`.

### Generate non-interactively

```powershell
$batch = @"
Key-Type: RSA
Key-Length: 3072
Name-Real: Nova Ops Audit
Name-Email: ops-audit@example.com
Expire-Date: 0
%no-protection
%commit
"@
$batch | Set-Content gpg-batch.txt -Encoding ASCII
gpg --batch --pinentry-mode loopback --generate-key gpg-batch.txt
Remove-Item gpg-batch.txt
```

> For production, use `%no-protection` only if keys are stored securely (e.g., encrypted disk or secrets manager).

### Export the public key

```powershell
gpg --batch --yes --armor --output trust/vault_public.gpg --export "Nova Ops Audit"
```

## 4. Re-sign Vault Manifest

After refreshing keys or editing the manifest, regenerate signatures and checksums:

```powershell
# GPG signature
gpg --batch --yes --pinentry-mode loopback --armor `
    --output attest/archives/vault.manifest.yaml.asc `
    --detach-sign attest/archives/vault.manifest.yaml

# cosign signature
set COSIGN_PASSWORD=password123
set COSIGN_YES=true
.\\tools\\audit\\cosign.exe sign-blob `
    --key %USERPROFILE%\\.nova\\trust\\cosign.key `
    --output-signature attest\\archives\\vault.manifest.sig `
    attest\\archives\\vault.manifest.yaml

# Checksums
python -c "import hashlib, pathlib; base=pathlib.Path('attest/archives'); files=['vault.manifest.yaml','vault.manifest.yaml.asc','vault.manifest.sig']; lines=[f'{hashlib.sha256((base/f).read_bytes()).hexdigest()}  attest/archives/{f}' for f in files]; (base/'Nova_Continuity_Vault.sha256').write_text('\n'.join(lines)+'\n')"
```

Finally re-run the audit:

```bash
python scripts/verify_vault.py
```

## 5. Automation Considerations

An autonomous agent can follow these steps programmatically:

1. Execute `scripts/bootstrap_audit_tools.py`.
2. Generate cosign keys using environment variables for secrets.
3. Generate/import the GPG key via batch input.
4. Export public keys and re-sign the manifest.
5. Update `attest/archives/Nova_Continuity_Vault.sha256` and run the audit.

Consider wrapping the process in a single orchestration script if regular rotations are required.
