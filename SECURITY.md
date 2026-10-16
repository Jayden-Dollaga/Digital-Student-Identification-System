# Security Policy

This repository's active product uses a local, desktop-first security model. The application stores the primary auth state and attendance data on disk in the local `data/` directory, but authorization is enforced in memory through the active session and backend checks.

## Security model

- There is no default administrator password.
- The initial admin password is created during the first-run wizard.
- Passwords are stored using PBKDF2-HMAC-SHA256 with a random salt.
- Session role elevation is checked in memory, not by trusting a stored role value in `data/settings.json`.
- Guest-to-Teacher elevation is denied by the backend; teacher mode can only be selected from an authenticated administrator session. Admin elevation remains password-gated. See [the implementation security model](docs/Security/security-model.md).
- Backend permission checks protect record reads and privileged mutations. Some diagnostic/aggregate bridge methods remain available without record-read permission; UI control visibility is not authorization.

## Data sensitivity

Treat the following as sensitive local-school data:

- `data/settings.json`
- `data/attendance.db`
- `data/backups/`
- `data/logs/`
- `data/exports/`
- any admin auth marker files created during the first-run flow

Protect these files with appropriate Windows ACLs and avoid storing them in shared or public directories.

The AES-GCM RFID application key is stored in `data/settings.json` and is not encrypted at rest. The `get_settings()` bridge method omits RFID key material, but anyone who can read the data directory can still obtain it. Do not treat RFID payload encryption as protection from someone with access to the application data files.

Database backups use SQLite's online backup API so committed WAL data is included. Restore checks path containment, file type, SQLite header, and SQLite `quick_check` before replacing the live database.

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
