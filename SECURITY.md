# Security Policy

This repository's active product uses a local, desktop-first security model. The application stores the primary auth state and attendance data on disk in the local `data/` directory, but authorization is enforced in memory through the active session and backend checks.

## Security model

- There is no default administrator password.
- The initial admin password is created during the first-run wizard.
- Passwords are stored using PBKDF2-HMAC-SHA256 with a random salt.
- Session role elevation is checked in memory, not by trusting a stored role value in `data/settings.json`.
- The current role selector permits Guest-to-Teacher without password verification. Teacher permissions include record reads, exports, and backups; do not rely on Guest mode as a confidentiality boundary. See [the implementation security model](docs/Security/security-model.md).
- Backend permission checks exist for many privileged operations, but not every public bridge method is role-gated. Consult the method-level [application inventory](docs/generated/APP_INVENTORY.md); UI control visibility is not authorization.

## Data sensitivity

Treat the following as sensitive local-school data:

- `data/settings.json`
- `data/attendance.db`
- `data/backups/`
- `data/logs/`
- `data/exports/`
- any admin auth marker files created during the first-run flow

Protect these files with appropriate Windows ACLs and avoid storing them in shared or public directories.

The AES-GCM RFID application key is stored in `data/settings.json`. The current unguarded `get_settings()` bridge method returns this key to JavaScript (while removing the password hash record). Do not treat RFID payload encryption as protection from someone who can interact with the running app; the key is also not encrypted at rest by this application.

## Reset and recovery

There is no in-app forgotten-password recovery procedure. A database backup does not include `settings.json` or restore the administrator password. `change_admin_password` requires the current password, and first-run setup refuses to replace an initialized password. Do not delete or edit the settings file or initialization marker as an improvised reset; contact the maintainer for a supported recovery path.

## Reporting a vulnerability

Email the maintainer at: [jaydendollaga4@gmail.com](mailto:jaydendollaga4@gmail.com)

Please include:

- the vulnerability and affected component
- the version or commit in use
- reproduction details if safe to share
- impact and suggested mitigation

Do not disclose a vulnerability publicly before it has been assessed.

## Additional guidance

See:

- [docs/Security/security-model.md](docs/Security/security-model.md)
- [docs/INDEX.md](docs/INDEX.md)
- [LICENSE](LICENSE)

The archived UI work under `archive/legacy-ui/` is historical and is not the supported product boundary for current security review.
