# pywebview Bridge Contract

The v3 frontend and Python backend communicate through pywebview. The bridge is the application's local RPC-style boundary.

## How the bridge is created

`python/gui_web/main_web.py` creates an `Api` instance and passes it to:

    webview.create_window(
        title="DSIS — Digital Student Identification System",
        url=str(index_path),
        js_api=api,
        width=1180,
        height=740,
        min_size=(900, 600),
    )

After pywebview exposes the object, JavaScript calls methods through:

    window.pywebview.api.method_name(...)

The frontend waits for the `pywebviewready` event before using the API.

## Event push model

Python uses `Api._push(event, payload)` to call the frontend's:

    window.dsisEvent(event, payload)

Current event names handled by `app.js`:

- `scan_result`
- `serial_line`
- `log_line`
- `enroll_progress`
- `delete_progress`
- `wipe_progress`
- `fingerprint_count`
- `connection_status`
- `connection_changed`
- `connection_troubleshooting`
- `serial_error`
- `data_changed`
- `mode_changed`

Nested progress event values include `success`, `error`, `cancelled`, `start`, `enrolling`, and `step`.

## Authorization rule

The JavaScript UI may hide buttons or disable controls, but that is not the security boundary.

Privileged actions are checked again in the Python bridge/core layer. The active role comes from the in-memory session in `core.permissions`.

## Complete public Api inventory

Every public method on `Api`, excluding private helpers and `__init__`, is recorded below.

| Method | Arguments | Access | Main effect / return |
| --- | --- | --- | --- |
| `_start_background_tasks` | none | private lifecycle hook | Starts automatic backup worker from Python host code |
| `_stop_background_tasks` | none | private lifecycle hook | Stops the worker from Python host code |
| `_set_window` | `window` | private lifecycle hook | Called from Python startup; not exposed as a public bridge method |
| `list_ports` | none | Guest | Returns COM port names |
| `list_ports_detailed` | none | Guest | Returns detailed COM-port metadata |
| `forget_saved_port` | none | Teacher or Administrator | Clears saved COM-port preference |
| `connect` | `port="", baud=0, auto_detect=None` | `scan`; Guest is restricted to saved/automatic port | Opens/validates ESP32 serial connection and persists connection preference |
| `disconnect` | none | Teacher or Administrator | Stops scanning/reconnect and closes serial connection |
| `get_connection_status` | none | Guest | Returns connection/device metadata |
| `start_scan` | none | `scan` | Sends `SCAN`; returns boolean |
| `stop_scan` | none | `scan` | Sends `STOP`; returns boolean |
| `start_enroll` | none | `enroll` | Sends enrollment command; begins enrollment state |
| `validate_student_fields` | student_no, student_name, grade, section | `enroll` | Returns per-field validation feedback; guards student-number existence check |
| `cancel_enroll` | none | `enroll` | Cancels active enrollment through stop handling |
| `discard_enrollment` | `fingerprint_id` | `delete` | Removes a partially stored fingerprint through the delete path |
| `delete_on_device` | `fingerprint_id` | `delete` | Sends `DELETE:id` and waits for device result |
| `wipe_all_on_device` | none | `wipe` | Sends `WIPE`; successful device wipe triggers local cleanup |
| `wipe_all_data` | none | `wipe` | Clears local student/attendance data |
| `request_fingerprint_count` | none | `scan` | Sends `LIST` and returns boolean |
| `get_serial_troubleshooting` | none | Guest | Returns serial troubleshooting information |
| `open_device_manager` | none | Guest | Opens Windows Device Manager helper |
| `open_driver_help` | none | Guest | Opens driver help/resource |
| `send_serial_command` | `cmd` | Administrator | Sends allow-listed diagnostic serial commands |
| `reset_device` | none | Administrator | Pulses DTR to intentionally reboot ESP32 |
| `get_dashboard_stats` | none | Requires `read_records`; Guest receives placeholders | Returns aggregate dashboard totals/status without disclosing counts to Guest |
| `get_recent_activity` | `limit=25` | `read_records` | Returns recent attendance rows with calculated status |
| `get_attendance` | `mode="today", offset=0` | `read_records` | Returns attendance page/range data |
| `export_attendance_csv` | `mode, offset, week_start` | `export` | Writes UTF-8 CSV using selected range |
| `get_students` | none | `read_records` | Returns enrolled students |
| `get_student` | `fingerprint_id` | `read_records` | Returns one student plus today's status |
| `mark_student_time_out` | `fingerprint_id` | Teacher or Administrator | Records an explicit departure after a qualifying Time In; rejects duplicate Time Out |
| `save_student` | student fields, optional previous ID | `enroll` | Creates/updates student or migrates fingerprint ID |
| `delete_student` | `fingerprint_id` | `delete` | Deletes local student record; historical attendance becomes ID 0 |
| `export_students_csv` | none | `export` | Writes student CSV |
| `get_attendance_evaluation` | `period="month", ref_date=""` | `attendance_evaluation` + `read_records` | Returns day/week/month per-student evaluation |
| `export_attendance_evaluation_csv` | same as evaluation | `export` plus evaluation/read checks | Calls evaluation then exports CSV |
| `get_calendar_month` | `year, month` | Guest | Returns calendar exceptions for month |
| `set_calendar_entry` | date, type, label, optional times | `manage_calendar` | Writes holiday/suspension/half-day entry |
| `remove_calendar_entry` | `date` | `manage_calendar` | Removes a stored calendar entry |
| `get_statistics_report` | none | `read_records` plus `export` or `backup` | Returns identifiable attendance/student summary data |
| `export_statistics_report` | none | `export` | Writes statistics report |
| `list_backups` | none | `backup` | Lists database backups and verified pre-restore safety snapshots |
| `create_backup` | none | `backup` | Creates timestamped database copy |
| `restore_backup` | `backup_path` | `restore` | Validates location/type/header and replaces live DB |
| `get_settings` | none | Guest | Returns sanitized settings/runtime metadata |
| `save_ui_settings` | `settings` | Administrator | Persists supported UI/attendance settings |
| `restore_default_settings` | none | Administrator | Replaces settings with defaults |
| `get_current_role` | none | Guest | Returns in-memory role |
| `set_current_role` | `role` | Session-aware | Switches role subject to session/password rules |
| `is_first_run_setup_required` | none | Guest | Reports whether first-run setup is needed |
| `complete_first_run_setup` | password, confirm_password | First-run only | Creates initial admin password and elevates to admin |
| `get_setup_wizard_step` | none | Guest | Returns next incomplete wizard step |
| `complete_setup_device_step` | `connected=False` | Administrator | Marks device step complete/skip state |
| `complete_setup_schedule_step` | time/thresholds/weekdays-off | Administrator | Saves schedule and marks step complete |
| `complete_setup_branding_step` | school_name, theme | Setup flow | Saves branding and marks final step |
| `authenticate_role` | `role, password` | Session-aware | Verifies role elevation and updates session |
| `get_session_state` | none | Guest | Returns current role/permissions/session state |
| `touch_session` | none | Guest | Extends active session idle timeout |
| `lock_session` | none | Guest | Returns active role to Guest |
| `change_admin_password` | current_password, new_password | Administrator | Verifies current password and writes new hash |
| `get_role_permissions` | `role` | Guest | Returns configured permission strings |
| `open_log_folder` | none | Administrator | Opens local log folder |
| `get_app_log` | `max_lines=500` | Administrator | Returns up to 1,000 recent application log lines |

- Repeated qualifying scans are audit events only; they do not mark departure. `mark_student_time_out` is the explicit, role-gated departure action. The configured schedule classifies arrival status but does not prove an individual student's departure.

## Important access details

- `request_fingerprint_count` is scan-permission gated even though it is read-only from the database perspective.
- `send_serial_command` accepts only the allow-listed diagnostic commands in the API and is Administrator-only.
- `reset_device` is Administrator-only.
- `save_ui_settings` is Administrator-only because it can change attendance/auth-adjacent runtime settings.
- `get_statistics_report` requires `read_records` plus either export or backup permission.
- `export_attendance_evaluation_csv` requires export permission and then reuses the attendance-evaluation and record-read checks.
- Frontend permission checks are UX controls; backend checks are authoritative.

## Return conventions

Most successful data-changing methods return a dictionary with `ok` plus message/result data. Read methods return dictionaries/lists directly. Boolean serial methods return true/false. Exact shapes should be checked against `python/gui_web/api.py` when changing the bridge.

