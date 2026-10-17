# Roles and Permissions

This guide describes the active v3 implementation. The main enforcement points are `python/config.py`, `python/core/permissions.py`, and backend checks in `python/gui_web/api.py`. Frontend button visibility is only a usability feature; the Python bridge is the authorization boundary.

## Configured permissions

| Role | Permission identifiers |
| --- | --- |
| Guest | `scan` |
| Teacher | `scan`, `read_records`, `export`, `backup`, `attendance_evaluation` |
| Administrator | `scan`, `read_records`, `enroll`, `delete`, `wipe`, `export`, `backup`, `restore`, `attendance_evaluation`, `manage_calendar` |

Permission checks are performed against the in-memory session. The `current_role` settings field is for UI continuity and cannot grant privileges.

## Authentication and role changes

- The app starts in Guest mode.
- A Guest session cannot switch directly to Teacher or Administrator. Those transitions require authentication; the administrator password is verified before elevation.
- An authenticated administrator can switch down to Teacher or Guest without re-entering the password.
- Non-Guest sessions expire after the configured idle timeout (10 minutes by default); locking the session returns it to Guest.
- Passwords are stored as salted PBKDF2-HMAC-SHA256 verifiers. Verification rejects malformed records and iteration values outside a bounded range.

## Data access and diagnostics

The roster, student detail, attendance history, recent activity, and identifiable attendance evaluation require record-reading permission. The evaluation API checks both `attendance_evaluation` and `read_records`; exporting that evaluation also requires `export`.

Student-field validation and enrollment cancellation require the `enroll` permission, since validation can reveal whether a student number is already registered and cancellation can change the device workflow. Reading recent application logs and opening the log directory are administrator-only because diagnostic data can include device identifiers and attendance-related details.

A small set of non-identifying helpers, such as port enumeration and aggregate dashboard metrics, remains available without `read_records`. Keep names, student numbers, scan timestamps tied to identifiable records, authentication data, and encryption keys out of those responses.

## RFID key and settings recovery

The RFID AES-GCM application key is removed from settings returned to JavaScript. Restoring ordinary settings preserves the key so enrolled encrypted cards are not invalidated. A malformed stored key is not silently rotated. Malformed JSON settings are moved to a timestamped `settings.json.corrupt-*` file before defaults are used; if the administrator initialization marker exists but the verifier is unavailable, the existing recovery-required state remains in effect. Back up the data directory securely before repair or re-enrollment.

## Limits of this security model

The desktop app is local-first, not a network service. Someone with direct USB/serial access to the ESP32 is inside the physical trust boundary: the firmware's host-connected status is not cryptographic authentication. The on-device host gate reduces accidental commands; it does not prevent a person with direct serial access from spoofing that status. Local database, settings, log, backup, and export files also rely on OS account permissions and device encryption; the in-app password does not encrypt files against a user who can directly read them.

MIFARE Classic cards and plain UID checks are not clone-resistant credentials. The AES-GCM payload detects altered/forged payload bytes, but copying a complete valid payload onto a compatible cloned UID is a replay risk. Use fingerprint matching or a credential technology with a suitable challenge-response design when clone resistance is a requirement.

Last reviewed: 2026-10-18.
