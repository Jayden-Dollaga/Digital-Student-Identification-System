# Application Inventory

This document is the canonical code-level inventory for the maintained DSIS product. It records the supported runtime, the public API surface, the database model, and the active firmware boundary. When a historical note or an older doc disagrees with the code, this inventory reflects the code.

## 1. Active entry points

| Path | State | Notes |
| --- | --- | --- |
| `run_web_gui.py` | Active | Source launcher for the v3 desktop app. |
| `run_web_gui.bat` | Active | Windows convenience launcher. |
| `python/gui_web/main_web.py` | Active | Creates the native pywebview window and binds `Api`. |
| `Build/DSIS_v3.spec` | Active | PyInstaller spec for the current v3 package. |
| `python/main.py` | Archived/compat | Older launcher path; not the maintained entry point. |
| `archive/legacy-ui/` | Archived | Historical v1 and v2 UI code. |
| `python/gui_qt/` and `python/gui/` | Archived/reference | Legacy UI attachments and compatibility code. |

## 2. Public API surface (`python/gui_web/api.py`)

`Api` is exposed at `window.pywebview.api` and is the central JS-to-Python bridge. Methods return JSON-safe values or structured dictionaries. The backend continues to enforce permissions even if the UI hides a control.

### Connection and device management

- `list_ports()` → returns a list of detected serial ports.
- `list_ports_detailed()` → returns port metadata with device, VID:PID, and label.
- `forget_saved_port()` → clears the saved COM port, teacher/admin required.
- `connect(port="", baud=0, auto_detect=None)` → opens the serial port and starts the read loop.
- `disconnect()` → closes the serial device connection.
- `get_connection_status()` → reports connection state, port, and mode.
- `start_scan()` → sends the SCAN command and flips the device mode to scan.
- `stop_scan()` → stops scan mode.
- `request_fingerprint_count()` → sends LIST and requests a reply from the device.
- `get_serial_troubleshooting()` → returns connection diagnostics.
- `open_device_manager()` → opens Windows Device Manager.
- `open_driver_help()` → opens driver info.
- `send_serial_command(cmd)` → allow-listed raw command for admins.
- `reset_device()` → resets the connected device when permitted.

### Enrollment, deletion, and RFID

- `start_enroll()` → begins device enrollment and waits for firmware-progress events.
- `validate_student_fields(student_no, student_name, grade, section)` → validates the student form without writing.
- `cancel_enroll()` → cancels an active enrollment.
- `discard_enrollment(fingerprint_id)` → removes a not-yet-saved device template.
- `delete_on_device(fingerprint_id)` → sends DELETE:\<id\> and waits for firmware confirmation before local deletion.
- `wipe_all_on_device()` → sends WIPE for the attached device.
- `wipe_all_data()` → wipes local student and attendance rows without changing device fingerprints.
- `save_student(...)` → creates or updates a student row with a fingerprint ID.
- `delete_student(fingerprint_id)` → deletes the local student row only after the device confirms deletion.
- `start_rfid_register_session(...)` → starts RFID registration for a student record.
- `stop_rfid_register_session()` → ends the RFID-registration session.
- `start_batch_rfid_erase(unlink_registered=False)` → arms batch card erase logic.
- `stop_batch_rfid_erase()` → cancels an active RFID erase flow.
- `clear_student_card(fingerprint_id)` → removes a saved RFID link.

### Reporting and attendance

- `get_dashboard_stats()` → dashboard counts and summary values.
- `get_recent_activity(limit=25)` → recent attendance rows.
- `get_attendance(mode="today", offset=0)` → attendance query results by window.
- `export_attendance_csv(...)` → writes CSV exports.
- `get_students()` → all student rows.
- `get_student(fingerprint_id)` → one student row, including summary status.
- `export_students_csv()` → exports student roster to CSV.
- `get_attendance_evaluation(period="month", ref_date="")` → per-student attendance evaluation.
- `export_attendance_evaluation_csv(...)` → evaluation export.
- `get_calendar_month(year, month)` → reads calendar exceptions.
- `set_calendar_entry(...)` → sets holiday, suspension, or half-day entries.
- `remove_calendar_entry(date)` → removes a calendar exception.
- `get_statistics_report()` → overall report summary.
- `export_statistics_report()` → writes a text summary.

### Settings, auth, backups, logs

- `list_backups()` → lists backups.
- `create_backup()` → writes a timestamped DB backup to `data/backups/`.
- `restore_backup(backup_path)` → replaces the active SQLite database.
- `get_settings()` → reads the active settings object.
- `save_ui_settings(settings)` → persists UI settings.
- `restore_default_settings()` → resets settings to defaults.
- `get_current_role()` → returns the in-memory session role.
- `set_current_role(role)` → role selection with password requirement for admin elevation.
- `is_first_run_setup_required()` → reports setup state.
- `complete_first_run_setup(password, confirm_password)` → creates the initial admin hash.
- `get_setup_wizard_step()` → returns the next required step.
- `complete_setup_device_step(...)` → completes the device step.
- `complete_setup_schedule_step(...)` → saves schedule settings and completion.
- `complete_setup_branding_step(...)` → saves branding and completion.
- `authenticate_role(role, password)` → validates the password for the requested role.
- `get_session_state()` → reports session role, permissions, and timeout.
- `touch_session()` → refreshes the idle timeout.
- `lock_session()` → drops the session back to guest.
- `change_admin_password(current_password, new_password)` → rotates the password hash.
- `get_role_permissions(role)` → returns the configured permission strings.
- `open_log_folder()` → opens the log directory.
- `get_app_log(max_lines=500)` → returns recent log lines from the live run buffer.

## 3. Core modules and responsibilities

- `python/config.py` — project root, runtime config, default roles, and port heuristics.
- `python/settings_store.py` — default settings schema and persistence helpers.
- `python/core/auth.py` — password hashing, verification, validation, and first-run admin requirements.
- `python/core/permissions.py` — in-memory role/session model and authorization checks.
- `python/core/setup_wizard.py` — next-step router for password, device, schedule, and branding.
- `python/core/database.py` — SQLite schema, CRUD, validation, reports, backup/restore, and exports.
- `python/core/serial_handler.py` — COM port open/close, reconnect logic, and device reads/writes.
- `python/core/attendance.py` — fingerprint/card processing, confidence gating, cooldown, and attendance insertion.
- `python/core/attendance_status.py` — present/time-in/time-out and rule evaluation.
- `python/core/attendance_calendar.py` — calendar exceptions and school-day rules.
- `python/core/commands.py` — send-command wrappers for device actions.
- `python/core/device_discovery.py` — port heuristics and metadata discovery.
- `python/core/logger.py` — logs to console and rotating files, plus live UI logging.
- `python/core/rfid_card.py` — encrypted RFID payload creation and verification.
- `python/core/utils.py` — JSON parsing and helper logic.
- `python/services/student_service.py` — student-related service layer.
- `python/services/attendance_service.py` — attendance-related service layer.

## 4. SQLite schema and runtime data

The active database is `data/attendance.db`.

### `students`

Columns:

- `fingerprint_id INTEGER PRIMARY KEY`
- `student_no TEXT NOT NULL UNIQUE`
- `student_name TEXT NOT NULL`
- `grade TEXT NOT NULL`
- `section TEXT NOT NULL`
- `card_uid TEXT UNIQUE`
- `enrollment_date TEXT NOT NULL`
- `updated_date TEXT NOT NULL`

Indexed and validated fields include `student_no`, `card_uid`, and grade/section grouping.

### `attendance`

Columns:

- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `fingerprint_id INTEGER NOT NULL`
- `date TEXT NOT NULL`
- `time TEXT NOT NULL`
- `confidence INTEGER NOT NULL`
- `status TEXT NOT NULL`
- `timestamp TEXT NOT NULL`
- `event_type TEXT` (nullable, often `time_in` or `time_out`)

The application uses `fingerprint_id = 0` as a reserved placeholder for unregistered or unknown scans. Student deletion preserves these rows by remapping them to ID 0 rather than losing the record entirely.

## 5. Data directory contents

The current runtime writes to the local `data/` directory:

- `settings.json` — UI settings, auth hash, wizard progress, and local preferences
- `.admin_initialized` — written after the initial admin password is created
- `attendance.db` — primary SQLite database
- `backups/` — timestamped database snapshots
- `logs/` — rotating app logs
- `exports/` — CSV exports and report output

## 6. Active firmware and protocol

The active sketch is:

- `firmware/ESP32_DSIS_AllInOne/ESP32_DSIS_AllInOne.ino`

It identifies itself as:

- device: `Digital Student Identification System`
- board: `ESP32`
- firmware: `1.6.2`
- sensor: `AS608`
- protocol: `1`

### Serial boundary

- PC to ESP32: 115200 baud
- ESP32 to AS608: 57600 baud

### Commands

- `ID?`
- `SCAN`
- `STOP`
- `LIST`
- `ENROLL`
- `ENROLL:<id>`
- `DELETE:<id>`
- `WIPE`
- `STATUS:<state>`

### Device output notes

The firmware emits text and JSON payloads including scan matches, mode transitions, enrollment progress, delete/wipe progress, and card events. Fingerprint IDs are in the 1-127 range, and the firmware restricts recognition attempts to a minimum confidence threshold and a device-level cooldown.

## 7. Role model and first-run wizard

Roles are defined in `python/config.py` and enforced in `python/core/permissions.py`.

| Role | Permissions |
| --- | --- |
| `guest` | `scan`, `attendance_evaluation` |
| `teacher` | `scan`, `read_records`, `export`, `backup`, `attendance_evaluation` |
| `admin` | `scan`, `read_records`, `enroll`, `delete`, `wipe`, `export`, `backup`, `restore`, `attendance_evaluation`, `manage_calendar` |

The wizard order is:

1. password
2. device
3. schedule
4. branding

The password step is determined by the presence of the stored password hash, not by a separate settings flag.

## 8. Historical stack and archive boundary

- v1: CustomTkinter-based app
- v2: Qt/PySide-based app
- v3: HTML/pywebview desktop app

The v1 and v2 sources remain in `archive/legacy-ui/` and other legacy directories for lineage, regression reference, and historical comparison. They are not the current operating or support path.

## 9. Behavioral evidence from tests

The active tests treat the following behaviors as required:

- salted password hashing and verification
- guest-to-teacher/admin elevation rules
- admin password requirement for privilege changes
- in-memory role authorization rather than `settings.json`-based trust
- attendance row event tagging and evaluation logic
- backup and restore validation
- database initialization and ID 0 placeholder handling

This is the same source-of-truth boundary used by the docs in this repository.
