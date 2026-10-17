# DSIS Security Model

This document summarizes the implementation for security reviewers. The public reporting process remains in the repository-root [SECURITY.md](../../SECURITY.md).

## Authentication

The first-run wizard creates the initial administrator password.

Implementation values:

- password length: 8–1,024 characters,
- PBKDF2-HMAC-SHA256,
- random 16-byte salt and 32-byte digest,
- 310,000 iterations for newly created passwords,
- accepted persisted iteration range: 100,000–1,000,000 (invalid records fail closed).

Five failed administrator-password attempts trigger a 30-second lockout. The attempt counter and epoch-based lockout deadline are persisted inside the private `auth` settings record, so restarting the app does not immediately clear the lockout. Password verification is serialized with password changes to avoid parallel attempts racing the counter.

The password-derived record is stored under `auth` in `data/settings.json`. The UI bridge strips the complete `auth` record and RFID key fields from settings responses.

## Session and role

The active role is process memory managed by `core.permissions`.

Role levels:

    guest < teacher < admin

Default authenticated idle timeout: 600 seconds.

`touch_session()` refreshes an active session. `lock_session()` returns to Guest. Expiration also returns to Guest.

`current_role` in `settings.json` is not an authorization source. Guest may scan, but `get_dashboard_stats()` returns restricted placeholders unless the active role has `read_records`. That permission is required for roster, student details, attendance history, dashboard aggregates, statistics reports, and identifiable evaluation rows. Evaluation CSV export additionally requires `export`. Guest permissions are scan-only.

`set_current_role("teacher")` requires an existing authenticated administrator session; Guest-to-Teacher is denied. Admin elevation remains password-gated. Some diagnostic bridge methods (for example port listing and sanitized settings) remain available without `read_records`; avoid adding student-identifiable data to those responses.

First-run password creation is protected by `data/.admin_initialized`. If settings lose the password after that marker exists, the application reports a recovery state instead of creating a new administrator password.

The firmware accepts destructive commands only after the host sends `HOST_CONNECTED` following the DSIS identity handshake. This is not cryptographic authentication: the same public serial parser accepts `STATUS:HOST_CONNECTED` and JSON status messages, so anyone with direct USB serial access can set the flag and then issue destructive commands. Treat direct serial access as trusted physical access; this gate only reduces accidental direct commands.

## Attendance integrity

Only fingerprint matches at or above the configured raw AS608 confidence threshold (1–255; default 100) are inserted as attendance. Below-threshold regular hardware matches are diagnostic-only `WEAK MATCH` results. The firmware floor remains 50. Attendance evaluation enumerates elapsed scheduled weekdays and calendar exceptions rather than inferring school days from whether a scan happened; future dates in the current period are not counted.

Student-field uniqueness validation, enrollment cancellation, RFID session stop controls, identifiable statistics reports, log viewing/opening, and evaluation CSV export have backend permission checks. The log API clamps reads to 1,000 lines and is Administrator-only. Backend checks are required even if the frontend hides the control.

## Permission enforcement

The default role permissions are:

| Role | Permissions |
| --- | --- |
| Guest | scan |
| Teacher | scan, read_records, export, backup, attendance_evaluation |
| Administrator | scan, read_records, enroll, delete, wipe, export, backup, restore, attendance_evaluation, manage_calendar |

Privileged API/core paths perform the authorization checks. UI visibility is not treated as security.

## High-impact operations

Security review should pay particular attention to:

- enrollment and student persistence,
- device deletion and wipe,
- raw diagnostic serial commands,
- settings changes,
- backup creation,
- restore replacement,
- password changes,
- calendar modification,
- CSV export.

## Local data

Protect:

    data/settings.json
    data/attendance.db
    data/backups/
    data/logs/
    data/exports/
    data/charts/

These locations can contain student information, attendance history, authentication material, RFID key material, or diagnostic records. The AES-GCM RFID key is stored in `data/settings.json` without encryption at rest. Settings writes use a temporary file, flush/fsync, and atomic replacement. Malformed JSON or non-object settings are moved to a timestamped `settings.json.corrupt-*` file rather than silently discarded; unreadable files cause startup to fail. `get_settings()` omits key fields from its bridge response; protect the data directory with appropriate OS permissions and full-disk encryption (for example, BitLocker). A database backup does not contain the RFID key. See [settings recovery](settings-recovery.md).

## Restore containment

Backups use SQLite's online backup API to include committed WAL state. Restore resolves paths and requires the selected database to stay inside `data/backups/`; it then requires a `.db` extension, SQLite header, and successful `PRAGMA quick_check` before replacement.

## Password recovery

There is no forgot-password flow.

The first-run setup method refuses to overwrite an existing password record, and `change_admin_password` requires the existing password.

Deleting `settings.json` is not a supported password-reset mechanism. If a corrupted settings file has been quarantined, recover the trusted original settings/key first; do not treat the backup database alone as enough to recover encrypted cards.

## Reviewer checklist

Inspect:

- `python/gui_web/api.py`
- `python/core/permissions.py`
- `python/core/auth.py`
- `python/core/database.py`
- `python/core/serial_handler.py`
- `tests/test_v3_authentication.py`
- `tests/test_database_security.py`
- `tests/test_error_message_sanitization.py`
