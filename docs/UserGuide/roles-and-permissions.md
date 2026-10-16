# Roles and Permissions

This page records the current implementation, including a role-escalation limitation. The behavior below is not a recommendation for deploying identifiable student data. The source of truth is `python/config.py`, `python/core/permissions.py`, and the API checks in `python/gui_web/api.py`.

## Configured permissions

| Role | Permission identifiers |
| --- | --- |
| Guest | `scan`, `attendance_evaluation` |
| Teacher | `scan`, `read_records`, `export`, `backup`, `attendance_evaluation` |
| Administrator | `scan`, `read_records`, `enroll`, `delete`, `wipe`, `export`, `backup`, `restore`, `attendance_evaluation`, `manage_calendar` |

These are configured permission strings, not an exhaustive description of effective access. Some API methods have no direct role check, and a caller can invoke the local pywebview bridge independently of whether the frontend hides a control.

## Important limitation: Guest can select Teacher

`Api.set_current_role("teacher")` accepts the transition from Guest without password verification. The v3 authentication tests explicitly cover that behavior. Because Teacher includes `read_records`, `export`, and `backup`, a person with access to the running app can obtain those capabilities through the role selector. Do not rely on Guest mode to protect student records from an operator who can use the application. This is an implementation security limitation; it is not a supported authentication guarantee.

Administrator elevation from Guest or Teacher still requires the administrator password. The first-run administrator password is hashed using PBKDF2-HMAC-SHA256. Reverting from Admin to Teacher or Guest does not require another password.

## Effective access details

- Guest can scan and read the aggregate values returned by `get_dashboard_stats()`, which has no direct API role check. Guest cannot read the roster or attendance history through methods gated by `read_records`.
- `get_attendance_evaluation()` requires both `attendance_evaluation` and `read_records`. Although Guest has the former configured, Guest does not receive identifiable evaluation rows; the API returns an error.
- Teacher is configured for record reading, export, and backup creation/listing. The role-selector limitation above means those configured capabilities are not currently password-protected from Guest.
- Administrator is configured for all listed permissions, including restore and calendar management. Several settings, log, and serial status APIs have their own checks or no direct role check; consult the [full API inventory](../generated/APP_INVENTORY.md) for method-level behavior.

## Session lifecycle

The API initializes the process as Guest. Non-Guest sessions expire after the configured idle timeout (default 10 minutes / 600 seconds); explicit `touch_session()` refreshes it, and `lock_session()` returns to Guest. Expiration is evaluated when the in-memory permission model is queried. The `current_role` setting in `data/settings.json` is not used by `core.permissions` to authorize actions.

## Backend and UI checks

The frontend hides or disables controls for convenience, but that is not authorization. The API and shared command helpers enforce checks at many operations; not every public API method has a role check. See the method-by-method notes in the [application inventory](../generated/APP_INVENTORY.md). Tests in `tests/test_v3_authentication.py` include the Guest-to-Teacher transition and should be read as evidence of current behavior, not evidence that the transition is secure.

## Attendance evaluation

The `attendance_evaluation` permission is configured for all roles, but the current API also requires `read_records`. Therefore only Teacher and Administrator sessions can obtain identifiable evaluation output through the current method, subject to the Guest-to-Teacher limitation above.

Last reviewed: 2026-10-16.
