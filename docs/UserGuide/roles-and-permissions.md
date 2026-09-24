# Roles and Permissions

Authorization is session-based. The role in memory is the security boundary; the `current_role` setting is not.

## Role definitions

The defaults in `python/config.py` are:

| Role | Permissions | User management |
| --- | --- | --- |
| Guest | `scan` | No |
| Teacher | `scan`, `read_records`, `export`, `backup`, `attendance_evaluation` | No |
| Administrator | `scan`, `read_records`, `enroll`, `delete`, `wipe`, `export`, `backup`, `restore`, `attendance_evaluation`, `manage_calendar` | Yes |

The permission strings are literal configuration values.

## What each role can do

### Guest

Can scan and view aggregate/live status.

Cannot read the full roster or attendance history, enroll, delete, wipe, export, create/restore backups, or manage the calendar.

### Teacher

Can scan, read records, view attendance evaluation, export reports, and create backups.

Cannot enroll/delete/wipe, restore, or manage the school calendar.

### Administrator

Has all configured permissions. Administrator-only settings and role/password operations are also enforced by the API/session layer.

## Session lifecycle

The process begins as Guest.

Authenticating a role updates the in-memory role. Authenticated non-Guest sessions have an idle timeout of 600 seconds by default.

User activity calls `touch_session` and extends the active timeout.

`lock_session` immediately returns the session to Guest.

After expiry, permission checks observe Guest until a new authentication occurs.

## Role changes

Admin authentication requires the administrator password. A Guest cannot switch directly to Teacher; an Administrator may switch down to Teacher or Guest without re-authentication.

Teacher/Guest role changes follow the role hierarchy logic in `core.permissions`. Elevating to a higher role than the active session requires the necessary authentication rather than trusting `settings.json`.

Tests in `tests/test_v3_authentication.py` cover guest startup, role hierarchy, wrong-password behavior, lock/expiry, and rejected guest settings updates.

## UI versus backend authorization

The frontend uses permission state to hide/disable controls. That is only a user-interface convenience.

The actual privileged operations are checked in Python through `core.permissions` and API/core command logic. A caller that bypasses the UI should still be denied when the backend check applies.

## Attendance evaluation permission

All three default roles include `attendance_evaluation`. The report uses a dedicated permission rather than assuming that every reader is an administrator.
