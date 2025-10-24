# Nova vault trust material

- `cosign.pub` – public key used to verify `attest/archives/vault.manifest.sig`.
  The matching private key is expected at `%USERPROFILE%\.nova\trust\cosign.key`
  (outside the repository) when signatures need to be regenerated.
- `vault_public.gpg` – armored public key for the GPG signature of the vault
  manifest. The signing key lives in the maintainer's personal GPG keyring.

Do **not** commit private material under `trust/`. The `.gitignore` entry covers
`trust/cosign.key` and the `trust/private/` directory for any local storage.
