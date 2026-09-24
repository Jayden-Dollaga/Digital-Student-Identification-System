# DSIS Application Inventory

Code-first inventory of the maintained product at commit `37445e8`. Source and tests take precedence when this snapshot becomes stale.

## 1. Entry points and support boundary

| Surface | State | Description |
| --- | --- | --- |
| `run_web_gui.py` | Active | Source launcher for the v3 HTML/pywebview desktop application. |
| `run_web_gui.bat` | Active | Windows convenience launcher. |
| `python/gui_web/main_web.py` | Active | Creates the pywebview window, attaches `Api`, and disconnects on close. |
| `Build/DSIS_v3.spec` | Active | PyInstaller specification for the v3 package. |
| `Build/DSIS_v3/` | Generated | v3 distribution output. |
| `python/main.py` | Legacy/verify | Retained compatibility launcher; not the documented product path. |
| `archive/legacy-ui/v1` | Archived | CustomTkinter application. |
| `archive/legacy-ui/v2` | Archived | PySide6/Qt application. |
| `python/gui_qt/`, `python/gui/legacy/` | Archived/reference | Historical UI code only. |

The active firmware is `firmware/ESP32_DSIS_AllInOne/ESP32_DSIS_AllInOne.ino`, which includes AS608 fingerprint and RC522 RFID support. `firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino` is the earlier fingerprint-only variant and is not the feature-complete target.

## 2. Public `Api` methods

All methods below are callable as `window.pywebview.api.<method>`. Return values are JSON-compatible unless noted. Failed operations normally return `{ok: false, message: ...}`. Python authorization remains authoritative even when JavaScript hides a control.

### Lifecycle and device

| Method and arguments | Return | Permission | Effects |
| --- | --- | --- | --- |
| `start_background_tasks()` | `None` | lifecycle | Starts the daemon auto-backup loop. |
| `stop_background_tasks()` | `None` | lifecycle | Stops the backup loop. |
| `set_window(window)` | `None` | lifecycle | Attaches the native window and starts background work. |
| `list_ports()` | `list[str]` | guest | Reads available serial ports. |
| `list_ports_detailed()` | `list[dict]` | guest | Reads port device, VID/PID, and description. |
| `forget_saved_port()` | `dict` | guest | Writes an empty saved COM port. |
| `connect(port="", baud=0, auto_detect=None)` | `dict` | guest | Opens serial, performs device discovery/handshake, and starts reads. |
| `disconnect()` | `dict` | guest | Stops reads and closes serial. |
| `get_connection_status()` | `dict` | guest | Reads connection/device state. |
| `start_scan()` | `bool` | `scan` | Sends `SCAN` and changes device mode. |
| `stop_scan()` | `bool` | `scan` | Sends `STOP` and exits scan mode. |
| `request_fingerprint_count()` | `bool` | guest | Sends `LIST`; result arrives asynchronously. |
| `get_serial_troubleshooting()` | `dict` | guest | Returns connection diagnostics. |
| `open_device_manager()` | `dict` | guest | Opens Windows Device Manager. |
| `open_driver_help()` | `dict` | guest | Opens driver guidance. |
| `send_serial_command(cmd)` | `bool` | guest | Sends a raw serial command. |
| `reset_device()` | `bool` | guest | Sends the device reset/stop command. |

### Enrollment, deletion, and RFID

| Method and arguments | Return | Permission | Effects |
| --- | --- | --- | --- |
| `start_rfid_register_session(fingerprint_id, mode="register")` | `dict` | admin + `enroll` | Arms RFID register/read mode and changes serial state. |
| `stop_rfid_register_session()` | `dict` | session | Stops RFID mode and restores prior state. |
| `start_batch_rfid_erase(unlink_registered=False)` | `dict` | `enroll` | Starts batch card erase; can unlink local UIDs. |
| `stop_batch_rfid_erase()` | `dict` | session | Cancels batch erase. |
| `start_enroll()` | `dict` | `enroll` | Starts device enrollment tracking. |
| `validate_student_fields(student_no, student_name, grade, section)` | `dict` | guest | Validates without writing. |
| `cancel_enroll()` | `dict` | `enroll` | Cancels pending device enrollment. |
| `discard_enrollment(fingerprint_id)` | `dict` | `enroll` | Removes staged local enrollment data. |
| `delete_on_device(fingerprint_id)` | `dict` | `delete` | Sends device delete and coordinates local cleanup after success. |
| `wipe_all_on_device()` | `dict` | `wipe` | Sends destructive device wipe. |
| `wipe_all_data()` | `dict` | `wipe` | Destructively clears local student and attendance data. |
| `save_student(fingerprint_id, student_no, student_name, grade, section, previous_fingerprint_id)` | `dict` | `enroll` | Writes or updates a student row. |
| `bind_student_card(fingerprint_id, card_uid)` | `dict` | `enroll` | Writes a normalized UID link. |
| `clear_student_card(fingerprint_id)` | `dict` | `enroll` | Removes a local UID link. |
| `delete_student(fingerprint_id)` | `dict` | `delete` | Deletes the profile and remaps retained attendance to ID 0. |

### Reads, attendance, reports, and calendar

| Method and arguments | Return | Permission | Effects |
| --- | --- | --- | --- |
| `get_dashboard_stats()` | `dict` | guest | Reads dashboard totals. |
| `get_recent_activity(limit=25)` | `list[dict]` | guest | Reads recent attendance. |
| `get_attendance(mode="today", offset=0)` | `dict` | guest | Reads attendance rows. |
| `export_attendance_csv(mode, offset, week_start)` | `dict` | `export` | Writes a selected CSV. |
| `get_students()` | `list[dict]` | guest | Reads roster. |
| `get_student(fingerprint_id)` | `dict` | guest | Reads one profile. |
| `export_students_csv()` | `dict` | `export` | Writes a student CSV. |
| `get_attendance_evaluation(period="month", ref_date="")` | `dict` | `attendance_evaluation` | Calculates day/week/month evaluation. |
| `export_attendance_evaluation_csv(period="month", ref_date="")` | `dict` | `export` | Writes evaluation CSV. |
| `get_calendar_month(year, month)` | `dict` | guest | Reads calendar exceptions. |
| `set_calendar_entry(date, entry_type, label, time_in, time_out)` | `dict` | `manage_calendar` | Writes holiday, suspension, or half-day settings. |
| `remove_calendar_entry(date)` | `dict` | `manage_calendar` | Removes a calendar exception. |
| `get_statistics_report()` | `dict` | export or backup | Reads report metrics. |
| `export_statistics_report()` | `dict` | `export` | Writes report output and optional charts. |

### Backup, settings, auth, and logs

| Method and arguments | Return | Permission | Effects |
| --- | --- | --- | --- |
| `list_backups()` | `list[dict]` | guest | Lists backup files. |
| `create_backup()` | `dict` | `backup` | Writes `data/backups/attendance_YYYYMMDD_HHMMSS.db`. |
| `restore_backup(backup_path)` | `dict` | `restore` | Validates and replaces the active DB. |
| `get_settings()` | `dict` | guest | Reads UI-safe settings. |
| `save_ui_settings(settings)` | `dict` | admin for protected settings | Persists permitted settings. |
| `restore_default_settings()` | `dict` | admin | Restores defaults. |
| `get_current_role()` | `str` | guest | Reads the in-memory role. |
| `set_current_role(role)` | `dict` | session rules | Switches role; admin elevation requires a password. |
| `is_first_run_setup_required()` | `dict` | guest | Reads first-run status. |
| `complete_first_run_setup(password, confirm_password)` | `dict` | first-run guest | Writes the initial password hash and sets admin. |
| `get_setup_wizard_step()` | `dict` | guest | Returns the next setup step. |
| `complete_setup_device_step(connected=False)` | `dict` | admin | Writes device-step completion. |
| `complete_setup_schedule_step(time_in, time_out, early_threshold_minutes, late_threshold_minutes, absent_threshold_minutes, school_weekdays_off)` | `dict` | admin | Writes schedule and weekday exceptions. |
| `complete_setup_branding_step(school_name="", theme="dark")` | `dict` | admin | Writes branding and completion. |
| `authenticate_role(role, password)` | `dict` | guest/session | Verifies and sets an in-memory role. |
| `get_session_state()` | `dict` | guest | Reads session role and timeout state. |
| `touch_session()` | `dict` | session | Refreshes idle expiry. |
| `lock_session()` | `dict` | session | Returns the session to guest. |
| `change_admin_password(current_password, new_password)` | `dict` | admin | Replaces the hash after verification. |
| `get_role_permissions(role)` | `list[str]` | guest | Returns configured permission names. |
| `open_log_folder()` | `dict` | guest | Opens the log directory. |
| `get_app_log(max_lines=500)` | `list[str]` | guest | Returns recent in-memory log lines. |

## 3. Maintained Python modules

- `core/auth.py`: password validation, salted PBKDF2-HMAC-SHA256 hashing, verification, and first-run password state.
- `core/permissions.py`: in-memory role session, role hierarchy, permission checks, and idle expiry. It never authorizes from `settings.json`.
- `core/database.py`: SQLite schema/migrations, validation, students, attendance, reports, exports, backups, restore, and ID 0 placeholder handling.
- `core/serial_handler.py`: COM open/close, serial reads/writes, reconnect, and connection state.
- `core/attendance.py`: fingerprint/card event processing, desktop cooldown, confidence filtering, and attendance writes.
- `core/attendance_status.py`: present/late/early/absent/half-day calculations.
- `core/attendance_calendar.py`: calendar exceptions and recurring school weekdays off.
- `core/commands.py`: serial command wrappers and privileged command checks.
- `core/device_discovery.py`: candidate-port discovery and device handshake metadata.
- `core/firmware_helper.py`: firmware asset discovery and descriptions.
- `core/logger.py`: console, rotating file, UI log buffering, and structured logging.
- `core/setup_wizard.py`: next-step selection for password, device, schedule, and branding.
- `core/rfid_card.py`: encrypted RFID payload operations.
- `core/utils.py`: JSON-line parsing and small shared helpers.
- `services/student_service.py`: service wrapper for student operations.
- `services/attendance_service.py`: service wrapper for attendance operations; some v3 API paths call core modules directly.

## 4. SQLite and migrations

Default file: `data/attendance.db`. Connections enable foreign keys and use a 30-second timeout.

`students` columns are `fingerprint_id INTEGER PRIMARY KEY`, `student_no TEXT NOT NULL UNIQUE`, `student_name TEXT NOT NULL`, `grade TEXT NOT NULL`, `section TEXT NOT NULL`, `card_uid TEXT UNIQUE`, `enrollment_date TEXT NOT NULL`, and `updated_date TEXT NOT NULL`. Indexes are the partial unique `idx_students_card_uid`, `idx_student_no`, and `idx_grade_section` on `(grade, section)`.

`attendance` columns are `id INTEGER PRIMARY KEY AUTOINCREMENT`, `fingerprint_id INTEGER NOT NULL`, `date TEXT NOT NULL`, `time TEXT NOT NULL`, `confidence INTEGER NOT NULL`, `status TEXT NOT NULL`, `timestamp TEXT NOT NULL`, and nullable `event_type`, with a foreign key to `students(fingerprint_id)`. Indexes are `idx_attendance_fingerprint_id`, `idx_attendance_date`, and `idx_attendance_timestamp`.

Initialization adds missing `card_uid` and `event_type` columns, backfills event types by student/date order (`time_in`, then `time_out`), removes invalid non-positive rows, and ensures permanent placeholder student ID 0 (`Unregistered`) exists. Student deletion remaps retained attendance to ID 0. Restore is replacement, not merge, and validates containment and SQLite structure first.

## 5. Runtime files under `data/`

- `settings.json`: connection, theme/branding, cooldown/confidence, logging, auto-backup, schedule, calendar, wizard flags, display role, and `auth` hash/salt/iteration data. It is sensitive; editing `current_role` does not elevate a session.
- `attendance.db`: local student/card and attendance data, unencrypted at rest.
- `backups/`: timestamped database snapshots.
- `logs/`: rotating runtime logs.
- `exports/`: user-selected CSV/report files.
- `charts/`: generated report charts when requested.

## 6. Active firmware and protocol

The active sketch is `firmware/ESP32_DSIS_AllInOne/ESP32_DSIS_AllInOne.ino` (firmware identifier `1.2.5`, protocol `1`). PC to ESP32 is 115200 baud; ESP32 UART2 to AS608 is 57600 baud. Fingerprint IDs are 1-127. AS608 uses ESP32 RX GPIO14 and TX GPIO27. RC522 uses SS/SDA GPIO5, RST GPIO4, MISO GPIO19, MOSI GPIO23, and SCK GPIO18.

Fingerprint commands are `ID?`, `SCAN`, `STOP`, `LIST`, `ENROLL`, `ENROLL:<id>`, `DELETE:<id>`, and `WIPE`. Host status messages use `STATUS:<state>`. The firmware implements `CARD_WRITE_HEX:<hex>` to arm a card write; the Python batch erase workflow coordinates erase/unlink behavior through the host protocol and does not rely on a separate `CARD_ERASE` command. Text output includes `READY`, `SCAN_MODE`, `CMD_MODE`, `ID:n`, `CONFIDENCE:n`, `UNKNOWN`, enrollment progress, delete/wipe results, and card results. JSON events include status, fingerprint match/unknown/low-confidence, and RFID card match/unreadable/write-result payloads. Firmware cooldowns are 2000 ms for fingerprints and 1500 ms for cards; Python applies configured desktop cooldown and minimum confidence.

## 7. Roles and setup

| Role | Permissions |
| --- | --- |
| `guest` | `scan`, `attendance_evaluation` |
| `teacher` | `scan`, `export`, `backup`, `attendance_evaluation` |
| `admin` | `scan`, `enroll`, `delete`, `wipe`, `export`, `backup`, `restore`, `attendance_evaluation`, `manage_calendar` |

Every launch starts guest. Admin elevation requires the configured password. Idle expiry defaults to 10 minutes and locking returns to guest. First-run order is password, device, schedule, branding; device connection may be deferred.

## 8. UI and behavioral tests

`python/gui_web/web/index.html` contains Dashboard, Attendance, Students, Reports, Logs, Settings, and Calendar pages plus first-run, authentication, password, enrollment, RFID, and calendar modals. `app.js` calls the bridge and consumes `window.dsisEvent`; `styles.css` provides presentation. There is no local web server.

`tests/test_v3_authentication.py` documents salted hashing, role hierarchy, first-run/elevation, expiry, and guest settings rejection. Attendance tests cover parsing, refresh, status, evaluation, export rows, and cooldown. Database tests cover initialization, reserved ID 0, reset, backup, restore containment, and reports. Serial, firmware-helper, dialog, UI-regression, and physical smoke tests cover remaining boundaries; physical tests require hardware.

## 9. Historical stack

v1 was CustomTkinter, v2 was PySide6/Qt, and v3 is HTML loaded in a native pywebview window. v1/v2 code and notes remain for lineage and comparison only. They are archived and unsupported as current launch or operating paths.
