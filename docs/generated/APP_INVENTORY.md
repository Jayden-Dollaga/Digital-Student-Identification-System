# DSIS Application Inventory

This document is the source-of-truth inventory for the maintained DSIS product. It records the actual application surfaces that exist in the current repository and reflects the code as it currently behaves.

## 1. Entry points

### Active launchers

- `run_web_gui.py` — current desktop launch file for the v3 app. Starts the pywebview window and exposes `Api` as `window.pywebview.api`.
- `run_web_gui.bat` — Windows convenience launcher for the same path.
- `python/gui_web/main_web.py` — explicit v3 window bootstrap and pywebview lifecycle manager.
- `python/main.py` — compatibility-style entry point, but the current maintained runtime is still the pywebview app.

### Packaging entry points

- `Build/DSIS_v3.spec` — active spec file for the packaged Windows build.
- `PORTABLE_BUILD.md` — documented Windows packaging flow.
- `Build/build-v3/` and `Build/DSIS_v3/` — generated output directories where packaged builds are produced.

### Archived launchers

- `archive/legacy-ui/v1` — legacy CustomTkinter implementation.
- `archive/legacy-ui/v2` — legacy Qt implementation.
- `python/gui_qt/` and `python/gui/legacy/` — retained for historical comparison, not active product launchers.

## 2. Public API methods on `python/gui_web/api.py`

The public methods are exposed as `window.pywebview.api.*`. They are the JS-to-Python integration boundary. The bridge is not an authorization boundary; permission enforcement remains inside `core.permissions` and the command layer.

| Method | Role / permission | Purpose | Side effects |
| --- | --- | --- | --- |
| `list_ports` | guest | List discovered serial ports | none |
| `list_ports_detailed` | guest | Detailed port metadata | none |
| `forget_saved_port` | guest | Clear saved COM port preference | writes settings |
| `connect` | guest | Connect to ESP32 | opens serial port |
| `disconnect` | guest | Close serial connection | closes serial port |
| `get_connection_status` | guest | Read connection metadata | none |
| `start_scan` | `scan` | Tell the device to enter scan mode | writes serial command |
| `stop_scan` | `scan` | Stop active scan mode | writes serial command |
| `start_enroll` | `enroll` | Begin enrollment flow | writes serial command, DB state transitions |
| `validate_student_fields` | guest | Validate student entry data | none |
| `cancel_enroll` | `enroll` | Cancel enrollment | writes serial command |
| `discard_enrollment` | `enroll` | Discard a partially stored fingerprint | DB writes |
| `delete_on_device` | `delete` | Delete one fingerprint from the sensor | writes serial command, DB writes |
| `wipe_all_on_device` | `wipe` | Wipe all fingerprints | writes serial command |
| `wipe_all_data` | `wipe` | Clear DB + student rows + attendance | destructive DB writes |
| `request_fingerprint_count` | guest | Ask device for count | writes serial command |
| `send_serial_command` | guest | Raw command to device | writes serial command |
| `reset_device` | guest | Reset device state | writes serial command |
| `get_dashboard_stats` | guest | Dashboard totals | DB read |
| `get_recent_activity` | guest | Recent attendance entries | DB read |
| `get_attendance` | guest | Attendance rows by mode/offset | DB read |
| `export_attendance_csv` | `export` | Export attendance rows to CSV | file write |
| `get_students` | guest | List student roster | DB read |
| `get_student` | guest | Fetch one student row | DB read |
| `save_student` | `enroll` or equivalent role logic | Save or update student record | DB write |
| `delete_student` | `delete` | Delete a student record | DB write |
| `export_students_csv` | `export` | Export student list | file write |
| `get_attendance_evaluation` | `attendance_evaluation` | Report attendance metrics | DB read |
| `export_attendance_evaluation_csv` | `export` | Export evaluation report | file write |
| `get_calendar_month` | guest | Calendar state for a month | settings read |
| `set_calendar_entry` | `manage_calendar` | Add holiday/suspension/half-day entry | settings write |
| `remove_calendar_entry` | `manage_calendar` | Remove a calendar entry | settings write |
| `get_statistics_report` | guest | Summary metrics | DB read |
| `export_statistics_report` | `export` | Export statistics report | file write |
| `list_backups` | guest | List backup archives | directory read |
| `create_backup` | `backup` | Create DB snapshot | file write |
| `restore_backup` | `restore` | Restore DB snapshot | DB overwrite |
| `get_settings` | guest | Read settings keys | disk read |
| `save_ui_settings` | guest | Persist UI settings | settings write |
| `restore_default_settings` | guest | Reset settings to defaults | settings write |
| `get_current_role` | guest | Read in-memory session role | none |
| `set_current_role` | guest | Set role for current session | session state |
| `is_first_run_setup_required` | guest | Check first-run status | none |
| `complete_first_run_setup` | guest | Create admin password | auth write |
| `get_setup_wizard_step` | guest | Get next step | none |
| `complete_setup_device_step` | guest | Mark device step done | settings write |
| `complete_setup_schedule_step` | guest | Mark schedule step done | settings write |
| `complete_setup_branding_step` | guest | Mark branding step done | settings write |
| `authenticate_role` | guest | Login as a role | session state |
| `get_session_state` | guest | Current session state | none |
| `touch_session` | guest | Refresh session timeout | session state |
| `lock_session` | guest | Lock current session | session state |
| `change_admin_password` | guest | Change password | auth write |
| `get_role_permissions` | guest | Return permission strings | none |
| `open_log_folder` | guest | Open logs folder | OS open |
| `get_app_log` | guest | Return recent log lines | none |

## 3. Core module inventory

### `python/core/auth.py`

Handles password creation, hashing, and verification. DSIS stores a salted PBKDF2-HMAC-SHA256 hash; there is no default admin password and no plaintext secret persisted.

### `python/core/permissions.py`

Provides authorization by in-memory session role. This is the security source-of-truth for permission checks. It explicitly refuses to trust `settings.json` as the role authority.

### `python/core/database.py`

Owns the SQLite schema, validation rules, attendance logging, backup/restore helpers, student CRUD, and export logic.

### `python/core/serial_handler.py`

Handles COM port discovery, device connections, reconnect logic, and low-level read/write operations for the ESP32.

### `python/core/attendance.py`

Processes scan lines into structured attendance events and applies cooldown logic before writes to the database.

### `python/core/attendance_status.py`

Calculates a student's attendance status using school-day rules, time windows, and exceptions.

### `python/core/attendance_calendar.py`

Stores and validates school calendar exceptions such as holidays, suspensions, and half-days.

### `python/core/commands.py`

Defines device command wrappers and role-gated command execution.

### `python/core/device_discovery.py`

Discovers viable ESP32 device candidate ports and handshake metadata.

### `python/core/firmware_helper.py`

Finds and describes firmware candidates for the project.

### `python/core/logger.py`

Configures the app logging system, including rotating file logs and UI log mirroring.

### `python/core/setup_wizard.py`

Determines the next incomplete setup step from the first-run wizard state.

### `python/core/utils.py`

Small parsing helpers such as JSON line extraction.

## 4. SQLite schema summary

The active database is created by `python/core/database.py` and defaults to `data/attendance.db`.

### Tables

- `students`
  - `fingerprint_id` INTEGER PRIMARY KEY
  - `student_no` TEXT NOT NULL UNIQUE
  - `student_name` TEXT NOT NULL
  - `grade` TEXT NOT NULL
  - `section` TEXT NOT NULL
  - `enrollment_date` TEXT NOT NULL
  - `updated_date` TEXT NOT NULL
- `attendance`
  - `id` INTEGER PRIMARY KEY
  - `fingerprint_id` INTEGER NOT NULL
  - `date` TEXT NOT NULL
  - `time` TEXT NOT NULL
  - `confidence` INTEGER NOT NULL
  - `status` TEXT
  - `event_type` TEXT
  - `timestamp` TEXT
  - foreign key to `students(fingerprint_id)`

### Special rules

- `fingerprint_id <= 0` rows are cleaned up.
- `fingerprint_id = 0` is treated as an unregistered placeholder and is not a real student.
- `event_type` is backfilled to `time_in` / `time_out` when older databases are migrated.
- `students` rows are ordered by `fingerprint_id` for roster lookups.

## 5. Runtime files under `data/`

The writable runtime directory is the working data area used by the app.

- `settings.json` — persisted settings, auth state, wizard progress, school calendar, theme, time rules, connection preferences.
- `attendance.db` — SQLite database for students and attendance logs.
- `backups/` — timestamped backup snapshots produced by DB backup logic.
- `logs/` — rotating log files and runtime logs.
- `exports/` — exported CSV reports.
- `charts/` — generated chart output if enabled.

## 6. Firmware protocol

The active firmware is at `firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino`.

### Connections and rates

- PC ↔ ESP32: 115200 baud
- ESP32 ↔ AS608: 57600 baud
- AS608 template IDs are treated as 1-127.

### Commands and outputs

- `ID?`
- `SCAN`
- `STOP`
- `LIST`
- `ENROLL`
- `ENROLL:<id>`
- `DELETE:<id>`
- `WIPE`
- `STATUS:<state>`

The app parser also accepts firmware lines indicating enrollment progress, wipe progress, scanned match results, and fingerprint totals. Cooldown logic exists both in the firmware/device path and in the Python desktop processor.

## 7. Roles and permissions

Roles are defined in `python/config.py`.

| Role | Permissions |
| --- | --- |
| `guest` | `scan`, `attendance_evaluation` |
| `teacher` | `scan`, `export`, `backup`, `attendance_evaluation` |
| `admin` | `scan`, `enroll`, `delete`, `wipe`, `export`, `backup`, `restore`, `attendance_evaluation`, `manage_calendar` |

The active auth model is session-based and in-memory. `settings.json` is not trusted as the source of role authority.

## 8. UI pages in `python/gui_web/web/`

The v3 interface is a browser-like frontend loaded from `python/gui_web/web/index.html` and powered by `app.js`.

- `index.html` — shell page and modal containers
- `app.js` — frontend application logic and API calls
- `styles.css` — UI styling

The live UI calls the backend through `window.pywebview.api` rather than through a local server.

## 9. Key tests describing current behavior

The repo's automated tests are evidence of actual intended behavior. Relevant examples include:

- authentication tests for first-run and password setup
- attendance tests for status, cooldown, and evaluation rules
- DB tests for reset, restore, and export logic
- serial and UI smoke tests for the local runtime

## 10. Historic stack and support boundary

- `archive/legacy-ui/v1` — CustomTkinter-era implementation
- `archive/legacy-ui/v2` — Qt-era implementation
- `python/gui_web` — current v3 webview-based application

The current product boundary is the v3 app. Older interfaces are kept for lineage, debugging, and comparison. They are not the maintained runtime path.
