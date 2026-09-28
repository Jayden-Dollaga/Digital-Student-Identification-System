# Security Policy

This repository's active product uses a local, desktop-first security model. The application stores the primary auth state and attendance data on disk in the local `data/` directory, but authorization is enforced in memory through the active session and backend checks.

## Security model

- There is no default administrator password.
- The initial admin password is created during the first-run wizard.
- Passwords are stored using PBKDF2-HMAC-SHA256 with a random salt.
- Session role elevation is checked in memory, not by trusting a stored role value in `data/settings.json`.
- Guest access is intentionally limited; teacher/admin access is granted only after authentication or a valid session.
- Device operations, restore operations, and export operations are gated by the backend permission model.

## Data sensitivity

Treat the following as sensitive local-school data:

- `data/settings.json`
- `data/attendance.db`
- `data/backups/`
- `data/logs/`
- `data/exports/`
- any admin auth marker files created during the first-run flow

Protect these files with appropriate Windows ACLs and avoid storing them in shared or public directories.

## Reset and recovery

The supported recovery path is a valid administrator-controlled backup or a legitimate password-change flow. There is no supported "delete `settings.json` and reset the password" procedure. The app intentionally prevents silent resets when the admin initialization marker and password state disagree.

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
