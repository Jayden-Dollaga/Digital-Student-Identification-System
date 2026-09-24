# DSIS Security Model

This document summarizes the implementation for security reviewers. The public reporting process remains in the repository-root [SECURITY.md](../../SECURITY.md).

## Authentication

The first-run wizard creates the initial administrator password.

Implementation values:

- minimum password length: 8,
- PBKDF2-HMAC-SHA256,
- random 16-byte salt,
- 310,000 iterations.

The password-derived record is stored under `auth` in `data/settings.json`.

## Session and role

The active role is process memory managed by `core.permissions`.

Role levels:

    guest < teacher < admin

Default authenticated idle timeout: 600 seconds.

`touch_session()` refreshes an active session. `lock_session()` returns to Guest. Expiration also returns to Guest.

`current_role` in `settings.json` is not an authorization source. Guest may scan and view aggregate/live status, but `read_records` is required for the roster, student details, attendance history, and identifiable attendance evaluation. Guest-to-Teacher/Admin elevation is rejected by `set_current_role`; authenticated role changes are required.

First-run password creation is protected by `data/.admin_initialized`. If settings lose the password after that marker exists, the application reports a recovery state instead of creating a new administrator password.

The firmware accepts destructive commands only after the host sends `HOST_CONNECTED` following the DSIS identity handshake. This is a protocol gate, not cryptographic authentication; anyone with direct serial access remains a physical-access threat.

## Permission enforcement

The default role permissions are:

| Role | Permissions |
| --- | --- |
| Guest | scan, attendance_evaluation |
| Teacher | scan, export, backup, attendance_evaluation |
| Administrator | scan, enroll, delete, wipe, export, backup, restore, attendance_evaluation, manage_calendar |

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

These locations can contain student information, attendance history, authentication material, or diagnostic records.

## Restore containment

Restore resolves paths and requires the selected database to stay inside `data/backups/`. It then requires a `.db` extension and SQLite header before replacement.

## Password recovery

There is no forgot-password flow.

The first-run setup method refuses to overwrite an existing password record, and `change_admin_password` requires the existing password.

Deleting `settings.json` is not a supported password-reset mechanism.

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
