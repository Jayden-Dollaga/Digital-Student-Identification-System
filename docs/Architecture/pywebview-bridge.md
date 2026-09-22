# pywebview Bridge Contract

The browser frontend communicates with Python through `window.pywebview.api`. That bridge is created in `python/gui_web/main_web.py` when the v3 app starts. The `Api` class in `python/gui_web/api.py` is the public contract used by the page.

## Bridge behavior

- Methods are exposed as `pywebview.api.<method_name>(...)`.
- Return values are JSON-serializable or raise exceptions that the frontend can handle as rejected promises.
- Python-originated updates are pushed through `_push(...)` as UI events.

## Event push model

The code uses `_push(event, payload)` to push app updates back to the frontend. This is the mechanism used for things like:

- log lines,
- device state changes,
- connection updates,
- scan events,
- attendance refreshes.

## Important security note

The JS front-end may hide a control, but that does not enforce authorization. Authorization still happens in Python via `core.permissions` and the actual API method logic.

## API summary

This is the current operational contract exposed by the v3 UI.

| API area | Examples |
| --- | --- |
| Serial and device | `connect`, `disconnect`, `list_ports`, `start_scan`, `stop_scan` |
| Enrollment | `start_enroll`, `cancel_enroll`, `save_student`, `delete_on_device` |
| Attendance | `get_attendance`, `get_recent_activity`, `export_attendance_csv` |
| Reports | `get_attendance_evaluation`, `export_attendance_evaluation_csv`, `get_statistics_report` |
| Calendar | `get_calendar_month`, `set_calendar_entry`, `remove_calendar_entry` |
| Settings and auth | `save_ui_settings`, `authenticate_role`, `change_admin_password`, `get_session_state` |
| Backups | `create_backup`, `restore_backup`, `list_backups` |
| Logs | `get_app_log`, `open_log_folder` |

The full method inventory is recorded in [docs/generated/APP_INVENTORY.md](../generated/APP_INVENTORY.md).
