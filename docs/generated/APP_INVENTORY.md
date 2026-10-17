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
This is the code-level inventory for the maintained DSIS product. It is a point-in-time snapshot of revision `b315de82a1248585b94994c49fef5c01e9ed54de`, reviewed 2026-10-16. Runtime code and tests are the evidence; historical reports and screenshots do not establish current behavior. No runtime source is changed by this inventory.

## Product boundary and launch

| Path | State and behavior |
| --- | --- |
| `run_web_gui.py` | Supported source launcher. Runs startup preflight, then launches `gui_web.main_web`. |
| `run_web_gui.bat` | Windows launcher; prefers `.venv\Scripts\python.exe`, then `python`. |
| `python/gui_web/main_web.py` | Creates pywebview native window, exposes `Api`, starts API background tasks, and disconnects on window close. |
| `python/gui_web/web/index.html`, `app.js`, `styles.css` | Frontend packaged by the current spec. No separately hosted web server is part of the supported runtime. |
| `Build/DSIS_v3.spec` | Current PyInstaller target; excludes Qt and CustomTkinter modules. Expected output described by `PORTABLE_BUILD.md`. |
| `python/startup_preflight.py` | Rejects Python outside 3.11-3.14, missing runtime imports, missing Windows WebView2, or an unwritable DB location; missing serial ports are a warning. |
| `python/main.py` | Compatibility entry point to the web UI; not the root-supported launcher. |
| `python/gui/legacy/`, `python/gui_web/v2_reference/`, `python/gui_qt/`, `archive/legacy-ui/`, `firmware/ESP32_Fingerprint_AllInOne/`, standalone sketches and `tests/Prototype/` | Legacy, reference, diagnostic, or experimental material; not the current supported launch/firmware path. |

The maintained UI has Dashboard, Attendance, Students, Reports, Calendar, Logs, and Settings pages. The webview bridge is `window.pywebview.api`; Python pushes frontend events through `window.dsisEvent(event, payload)`. The HTML includes first-run, enrollment, delete, RFID registration/erase, restore, authentication, and settings dialogs/workflows. These are local UI/process interfaces, not network APIs.

## Runtime prerequisites and packaging

Preflight supports Python 3.11 through 3.14 inclusive. It verifies imports for `serial`, `cryptography`, `openpyxl`, `matplotlib`, `PIL`, and `webview`; Windows additionally requires detected WebView2 Runtime. Port enumeration failure is a warning, not an app-start blocker. The project requirements also include legacy UI and development/test packages; package installation alone does not imply those stacks are maintained.

The source data root is `<project-root>/data`; in a frozen build it is the executable's parent directory. `FINGERPRINT_DB_PATH`, `FINGERPRINT_EXPORT_FOLDER`, and `FINGERPRINT_LOG_FOLDER` can override the corresponding paths. Settings are kept under the configured data directory. The app is local-first; this repository does not implement cloud synchronization or a remote service.

## Core modules

| Module | Responsibility and active callers |
| --- | --- |
| `python/config.py` | Runtime paths, environment overrides, defaults, role definitions, port scoring and shared `AppConfig`; used throughout active core/API. |
| `python/settings_store.py` | Defaults, JSON load/save, admin-initialization marker, stale saved-port cleanup. |
| `python/startup_preflight.py` | Environment/runtime checks before the root launcher imports the UI. |
| `python/gui_web/main_web.py` | Window setup, event lifecycle, exception hooks and API construction. |
| `python/gui_web/api.py` | JS/Python bridge, permission checks, serial read loop, workflow coordination, reports/settings/auth. |
| `python/core/auth.py` | Initial password validation, PBKDF2 hash creation and verification. |
| `python/core/permissions.py` | In-memory role/session state, role hierarchy and permission checks. |
| `python/core/setup_wizard.py` | Chooses next incomplete first-run step. |
| `python/core/database.py` | SQLite schema/init/migrations, student/attendance operations, reporting, backup/restore and export helpers. |
| `python/core/device_discovery.py` | Ranks/probes ports and validates DSIS identity/protocol handshake. |
| `python/core/serial_handler.py` | Serial connection, read/write, host status, buffer, disconnect and auto-reconnect. |
| `python/core/commands.py` | Serial command wrappers; enrollment/delete/wipe/card-write wrappers also check permissions. |
| `python/core/attendance.py` | Parses fingerprint/card events, resolves identity, applies app confidence/cooldown and records attendance. |
| `python/core/attendance_status.py` | Classifies time-in/time-out against schedule and thresholds. |
| `python/core/attendance_calendar.py` | Validates and stores holiday/suspension/half-day entries in settings JSON. |
| `python/core/rfid_card.py` | AES-GCM card payload encode/decode and local application key management. |
| `python/core/logger.py` | Console plus optional per-run file logging and old-log pruning. |
| `python/core/utils.py` | Shared JSON-line parsing and utility behavior. |
| `python/services/student_service.py`, `attendance_service.py` | Thin database wrappers; the active bridge primarily uses core modules directly. |

The active v3 import-boundary test enumerates `run_web_gui.py`, startup/config/settings, and `python/gui_web`, `python/core`, and `python/services` while excluding `v2_reference`; it asserts no legacy UI imports.

## Public bridge contract

Every public `Api` instance method below is exposed to JavaScript. Return values are JSON-safe scalar/list/dictionary values; a raised exception becomes a rejected pywebview promise. “No explicit role gate” means this method has no direct authorization check in the inspected implementation, not that the operation is safe for untrusted callers. `has_permission` and `require_permission` use the in-memory session and configured permissions.

| Method and arguments | Result | Authorization and effects |
| --- | --- | --- |
| `list_ports()` | `list[str]` | No role gate; enumerates ports. |
| `list_ports_detailed()` | `list[{device,label}]` | No role gate; includes USB description/VID:PID label when available. |
| `forget_saved_port()` | `{ok,...}` | Teacher-or-higher role; clears saved COM port in settings. |
| `connect(port="", baud=0, auto_detect=None)` | `{connected,message,port,baud,device_metadata}` | Requires `scan`; discovers/opens device, persists connection preference, starts reader, requests count. |
| `disconnect()` | `{connected}` or denial object | Teacher-or-higher role; stops scan/reader, resets operation state and closes serial. Window-close callback uses private `_disconnect_impl()` directly. |
| `get_connection_status()` | `{connected,port,baud,device_metadata,scanning,device_mode}` | No role gate; reports device state. |
| `start_scan()` / `stop_scan()` | `bool` | Require `scan`; send SCAN/STOP and update mode/event state. |
| `start_rfid_register_session(fingerprint_id, mode="register")` | `{ok,message}` | Requires connection and `enroll`, selected student must exist and scan must be stopped; starts card listening. |
| `stop_rfid_register_session()` | `{ok,message}` | Requires `enroll`; clears pending registration and stops listening when appropriate. |
| `start_batch_rfid_erase(unlink_registered=False)` | `{ok,message}` | Requires admin role and `enroll`, plus connection; arms card erase and optionally clears verified linked card. |
| `stop_batch_rfid_erase()` | `{ok,message}` | Requires Administrator role plus `enroll`; stops erase mode and restores prior scan state when possible. |
| `start_enroll()` | `{ok,message}` | Requires connection and `enroll`; sends STOP then ENROLL and waits for progress events. |
| `validate_student_fields(student_no, student_name, grade, section)` | `{all_valid,fields}` or denial | Requires `enroll`; guards the student-number existence check. |
| `cancel_enroll()` | `{ok,message}` or denial | Requires `enroll`; sends STOP for pending enrollment or clears local pending state on disconnect. |
| `discard_enrollment(fingerprint_id)` | `{ok,message}` | Requires `delete` and connection; deletes unsaved device template, no student DB write. |
| `delete_on_device(fingerprint_id)` | `{ok,message}` | Requires `delete` and connection; sends device command only; local row must wait for confirmed event. |
| `wipe_all_on_device()` | `{ok,message}` | Requires `wipe` and connection; sends device WIPE; API event handler clears local DB only after firmware success. |
| `wipe_all_data()` | `{ok,message,students,attendance}` | Requires `wipe`; clears local student/attendance records only; does not touch device. |
| `request_fingerprint_count()` | `bool` | Requires `scan` and connection; sends LIST. |
| `get_serial_troubleshooting()` | `{ports,message}` | No role gate; returns generic recovery instructions and enumerated ports. |
| `open_device_manager()` | `{ok,message?}` | No role gate; Windows-only `devmgmt.msc` launch. |
| `open_driver_help()` | `{ok,url,message?}` | No role gate; opens Silicon Labs driver page. |
| `send_serial_command(cmd)` | `bool` | Requires admin role; connected device and allow-list `LIST`, `HELP`, `COMMANDS`, `STOP`, `SCAN`, `ID?`. |
| `reset_device()` | `bool` | Requires admin role and connection; requests DTR reset. |
| `get_dashboard_stats()` | summary dictionary | No role gate; returns aggregate student/attendance counts and last scan time; do not add identifiable record fields without a permission check. |
| `get_recent_activity(limit=25)` | `list[attendance row]` | Requires `read_records`; otherwise empty list. |
| `get_attendance(mode="today", offset=0)` | `{rows,offset,has_more}` | Requires `read_records`; otherwise empty restricted result. Modes include today, last30, and paginated recent fallback. |
| `export_attendance_csv(mode="today", offset=0, week_start="")` | `{ok,message,path?}` | Requires `export`; writes selected records via Save As (or export dir without UI), UTF-8 BOM, formula-neutralized cells. |
| `get_students()` | `list[student row]` | Requires `read_records`; otherwise empty list. |
| `get_student(fingerprint_id)` | student dictionary or `{}` | Requires `read_records`; adds today's attendance status. |
| `save_student(fingerprint_id, student_no, student_name, grade, section, previous_fingerprint_id=0)` | `{ok,message}` | Requires `enroll`; creates/updates record or reassigns old fingerprint ID. |
| `bind_student_card(fingerprint_id, card_uid)` | `{ok:false,message}` | Always rejects; card links are saved only after verified card write/readback in registration flow. |
| `clear_student_card(fingerprint_id)` | `{ok,message}` | Requires `enroll`; clears local card UID. |
| `delete_student(fingerprint_id)` | `{ok,message}` | Requires `delete` and a prior confirmed device-delete event; DB keeps attendance by remapping rows to ID 0. |
| `export_students_csv()` | `{ok,message,path?}` | Requires `export`; exports roster plus today's time/status fields. |
| `get_attendance_evaluation(period="month", ref_date="")` | `{ok,period,start_date,end_date,total_days,school_days,rows}` or error | Requires both `attendance_evaluation` and `read_records`; reports per-student distinct days. |
| `export_attendance_evaluation_csv(period="month", ref_date="")` | `{ok,message,path?}` | Requires `export`, plus the delegated evaluation and record-read permissions; writes a CSV only after all checks pass. |
| `get_calendar_month(year, month)` | `{ok,year,month,entries}` or error | No role gate; reads settings calendar. |
| `set_calendar_entry(date, entry_type, label="", time_in="", time_out="")` | `{ok,date,entry}` or error | Requires `manage_calendar`; saves validated holiday/suspension/half-day settings. |
| `remove_calendar_entry(date)` | `{ok,date}` | Requires `manage_calendar`; removes entry from settings. |
| `get_statistics_report()` | report dictionary or error | Requires `read_records` plus `export` or `backup`; reads identifiable attendance and student summary data. |
| `export_statistics_report()` | `{ok,message,path?}` | Requires `export`; writes text report through Save As. |
| `list_backups()` | `list[backup metadata]` | Requires `backup`; otherwise empty list. |
| `create_backup()` | `{ok,message,path?}` | Requires `backup`; creates a database snapshot. |
| `restore_backup(backup_path)` | `{ok,message}` | Requires `restore`; replaces DB when validation passes and pushes `data_changed`. |
| `get_settings()` | settings dictionary | No direct role gate; removes `auth` and RFID key material, overlays in-memory role and ports, and includes backup metadata only for backup-capable/admin sessions. |
| `save_ui_settings(settings)` | `{ok}` or error | Requires admin; validates/clamps numeric schedule settings, removes caller-supplied `auth`, persists only known keys and applies selected live settings. |
| `restore_default_settings()` | `{ok,message}` | Requires admin; preserves auth and completed wizard flags, resets other defaults and live settings. |
| `get_current_role()` | role string | No role gate; returns in-memory effective role. |
| `set_current_role(role)` | session state or denial | Guest cannot switch directly to Teacher/Admin; authentication is required for elevation. Admin can demote to Teacher/Guest. |
| `is_first_run_setup_required()` | `{required,recovery_required}` | No role gate; reads API initialization state. |
| `complete_first_run_setup(password, confirm_password)` | `{ok,...session}` or error | Only while initial setup is required and not in recovery; validates password, saves hash/marker, elevates creator to admin. |
| `get_setup_wizard_step()` | `{step}` or recovery object | No role gate; reports next incomplete step. |
| `complete_setup_device_step(connected=False)` | `{ok}` | Requires current role exactly admin; marks device step complete even on explicit skip. |
| `complete_setup_schedule_step(time_in,time_out,early_threshold_minutes=15,late_threshold_minutes=15,absent_threshold_minutes=0,school_weekdays_off=None)` | `{ok}` or error | Requires admin; routes through settings validation then marks completion. |
| `complete_setup_branding_step(school_name="",theme="dark")` | `{ok}` or error | Requires admin; saves school name/theme and marks completion. |
| `authenticate_role(role,password)` | session state or `{ok:false,message}` | Admin password verification; 5 failed attempts trigger a persisted 30-second lockout across app restarts. Password length is bounded at 1,024 characters and PBKDF2 record parameters are validated. Non-admin branch only allows role transitions at or below current role. |
| `get_session_state()` | `{ok,role,permissions,idle_timeout_seconds}` | No role gate; reports in-memory role and configured permissions. |
| `touch_session()` | session state | No role gate; refreshes authenticated idle timer. |
| `lock_session()` | session state | No role gate; resets role to guest. |
| `change_admin_password(current_password,new_password)` | `{ok,message}` | Requires admin role and current password; new password minimum 8; same failed-attempt lockout state. |
| `get_role_permissions(role)` | `list[str]` | No role gate; returns configured permission strings. |
| `open_log_folder()` | `{ok}` or denial | Administrator-only; launches configured local log directory. |
| `get_app_log(max_lines=500)` | `list[str]` or empty list | Administrator-only; clamps reads to at most 1,000 recent lines. |
| `_start_background_tasks()` | `None` | Private Python lifecycle helper; not exposed as a public JavaScript bridge method. |
| `_stop_background_tasks()` | `None` | Private Python lifecycle helper; not exposed as a public JavaScript bridge method. |
| `_set_window(window)` | `None` | Private Python lifecycle helper; not exposed as a public JavaScript bridge method. |

### Authorization findings that affect documentation

Default permission identifiers in `python/config.py` are `scan`, `read_records`, `enroll`, `delete`, `wipe`, `export`, `backup`, `restore`, `attendance_evaluation`, and `manage_calendar`.

| Role | Configured permissions |
| --- | --- |
| `guest` | `scan` |
| `teacher` | `scan`, `read_records`, `export`, `backup`, `attendance_evaluation` |
| `admin` | `scan`, `read_records`, `enroll`, `delete`, `wipe`, `export`, `backup`, `restore`, `attendance_evaluation`, `manage_calendar` |

These lists are not a complete description of effective access. Guest-to-Teacher and Guest-to-Administrator transitions require authentication; Teacher includes record-read, export, and backup privileges. The evaluation API requires `read_records` in addition to `attendance_evaluation`, and CSV export additionally requires `export`. `get_app_log` and `open_log_folder` are Administrator-only. Limited aggregate/diagnostic helpers such as `get_dashboard_stats`, `get_calendar_month`, settings and port listing remain available without `read_records`; do not include identifiable student data in those results. UI visibility is not an authorization boundary.

Non-guest sessions default to a 600-second idle timeout. The timeout is refreshed through explicit `touch_session()` calls; lock or expiry returns to Guest. `settings.json`'s `current_role` is not used by `core.permissions` to authorize calls.

## Persistence model

The default database is `data/attendance.db` (path can be overridden with `FINGERPRINT_DB_PATH`). SQLite connections use a 30-second connect timeout, `busy_timeout=5000`, WAL journal mode, and `PRAGMA foreign_keys=ON`.

### Tables and indexes

| Table | Columns and constraints |
| --- | --- |
| `students` | `fingerprint_id INTEGER PRIMARY KEY`; `student_no TEXT NOT NULL UNIQUE`; `student_name TEXT NOT NULL`; `grade TEXT NOT NULL`; `section TEXT NOT NULL`; `card_uid TEXT UNIQUE` (nullable); `enrollment_date TEXT NOT NULL`; `updated_date TEXT NOT NULL`. |
| `attendance` | `id INTEGER PRIMARY KEY AUTOINCREMENT`; `fingerprint_id INTEGER NOT NULL`; `date TEXT NOT NULL`; `time TEXT NOT NULL`; `confidence INTEGER NOT NULL`; `status TEXT NOT NULL`; `timestamp TEXT NOT NULL`; `event_type TEXT` nullable; FK `fingerprint_id REFERENCES students(fingerprint_id)` without declared cascade. |

Indexes created by `init_database()`:

- `idx_students_card_uid`, unique partial index on `students(card_uid)` where non-NULL;
- `idx_student_no` on `students(student_no)`;
- `idx_grade_section` on `students(grade, section)`;
- `idx_attendance_fingerprint_id`, `idx_attendance_date`, and `idx_attendance_timestamp` on corresponding attendance columns.

There are no other application tables, database-backed settings, schema-version table, or migration history table in the active initialization code. The card UID column is added to older `students` tables when absent. The nullable `event_type` column is added to older `attendance` tables and missing values are backfilled in `fingerprint_id,date,time,id` order (first missing row per pair receives `time_in`, later missing rows `time_out`). Initialization removes negative-ID rows, but retains/creates reserved `students.fingerprint_id=0` with `N/A` values for unknown attendance. Normal student validation accepts fingerprint IDs 1-127. Student deletion remaps historical attendance to 0 before deleting the profile. Local data wipe deletes attendance and positive student IDs, leaving the placeholder.

`school_calendar` is **not** a SQL table. It is a settings JSON object keyed by `YYYY-MM-DD`; supported values are `holiday`, `suspension`, and `half_day` (the latter carries `time_in` and `time_out`). The attendance evaluation denominator enumerates elapsed scheduled weekdays, excluding configured no-class weekdays, weekends, holidays, and suspensions, regardless of whether any scan occurred; future dates are not counted in the active period. Each student's eligible denominator starts no earlier than their enrollment date. Empty eligible periods yield `attendance_rate: null` / `no_data`.

### Settings keys and runtime-created files

`python/settings_store.py` supplies defaults, merges known keys, saves atomically using a same-directory temporary file and atomic replace, and quarantines malformed JSON settings in a timestamped `settings.json.corrupt-*` file rather than discarding the only copy. If settings are quarantined and the RFID key is unavailable, key generation is blocked until recovery or deliberate re-enrollment. Defaults include: `com_port`, `baud_rate`, `cooldown`, `theme`, `auto_reconnect`, `auto_detect_serial`, `auto_connect_on_startup`, `startup_connect_delay_ms`, `compact_sidebar`, `enable_profiler`, `min_confidence`, `log_to_file`, `enable_debug_logging`, `current_role`, `rfid_payload_key`, `rfid_app_key_hex`, `rfid_aes_gcm_key`, `auto_backup_interval_minutes`, `time_in`, `time_out`, `early_threshold_minutes`, `late_threshold_minutes`, `absent_threshold_minutes`, `idle_timeout_minutes`, `auth`, `school_calendar`, `school_name`, `school_weekdays_off`, and the three `setup_*_step_done` flags. The Python API strips `auth` and all RFID key material from the settings object it returns to JavaScript. `current_role` is UI continuity only.

The legacy settings keys `rfid_payload_key` and `rfid_app_key_hex` remain in the defaults; current AES-GCM card payload logic uses `rfid_aes_gcm_key`. `get_settings()` removes `auth` and RFID key material before returning settings to JavaScript.

| Path | Content/owner |
| --- | --- |
| `data/settings.json` | Preferences, setup state, schedule/calendar, auth hash+salt, and locally stored RFID AES-GCM app key. It is not encrypted as a file. |
| `data/.admin_initialized` | Marker written after initial password setup; detects lost/corrupt auth state and prevents silent first-run recreation. |
| `data/attendance.db` | Student/card links and identifiable attendance history; SQLite file is not encrypted at rest by this app. |
| `data/backups/` | Timestamped `attendance_*.db` files created by copying the main DB file; copies inherit the data sensitivity of the database. |
| `data/logs/` | Optional timestamped per-run logs; retention pruning is bounded by configured backup count, not time. |
| `data/exports/` | Default output directory when no native save dialog is available; exports can also be saved to a user-selected path. |
| `data/charts/` | Database reporting/chart helpers may create chart artifacts. |

Never include actual settings, hashes, keys, student rows, logs, or production backups in documentation or source control. The `auth` record uses PBKDF2-HMAC-SHA256, random 16-byte salt, and 310,000 iterations. Verification checks decoded salt/digest lengths and rejects stored iteration counts outside 100,000–1,000,000 to prevent unbounded work from a malformed local verifier. Invalid settings files are quarantined instead of being silently overwritten; if an RFID key may have been lost with a quarantined settings file, new-key creation is blocked until explicit recovery or card re-enrollment. RFID application key material is locally persisted; AES-GCM card payload encryption does not encrypt the local settings/database/backups.

## Firmware and device protocol

Maintained sketch: `firmware/ESP32_DSIS_AllInOne/ESP32_DSIS_AllInOne.ino`, with RFID adapter code under `src/rfid/`. Identity constants are device `Digital Student Identification System`, board `ESP32`, firmware `1.6.2`, sensor `AS608`, protocol `1`. The sketch starts host `Serial` at 115200 and AS608 UART on `HardwareSerial(2)` at 57600, RX GPIO14/TX GPIO27. RC522 uses SPI with SDA/SS GPIO5, RST GPIO4, MISO GPIO19, MOSI GPIO23, SCK GPIO18; IRQ is not connected. AS608 initialization failure is reported but no longer blocks the main loop, so RC522 RFID scanning can continue; fingerprint-only commands are rejected while the sensor is offline.

| Host command | Behavior / gate |
| --- | --- |
| `ID?` | Returns JSON identity; used by host discovery. |
| `SCAN`, `STOP`, `LIST` | Switches mode, returns to command mode, or reports stored count. |
| `ENROLL`, `ENROLL:<id>` | Enroll next available or explicit ID 1-127. Requires firmware host-connected flag. Captures the same finger twice. |
| `DELETE:<id>`, `WIPE` | Delete one valid ID or all templates. Requires host-connected flag. |
| `CARD_WRITE_HEX:<96 hex chars>` | Arms 48-byte write; requires host-connected flag. Firmware validates length/hex and emits write result after write/readback. |
| `CARD_ERASE` | Arms verified 48-byte zero write; requires host-connected flag. |
| `CARD_KEYCHECK` | Arms Classic key check; diagnostic command, not in API raw-command allow-list. |
| `STATUS:<state>` or JSON `{"type":"status","state":"..."}` | Receives host state including `HOST_CONNECTED`/`HOST_DISCONNECTED`; host-connected gates destructive enroll/delete/wipe/card-write operations. This is not cryptographic device authentication. |

Identity JSON includes `device`, `board`, `firmware`, `sensor`, `protocol`, and ESP32 eFuse serial number. Discovery sends `ID?` and accepts matching identifier with integer protocol >=1; probe timeout is 3 seconds. It also checks unprompted boot identity before waiting for the reply, to handle sensor-failure boot output. Successful connection tells firmware `HOST_CONNECTED`; disconnect sends `HOST_DISCONNECTED` and STOP.

Firmware fingerprint match floor is confidence 50; its post-match delay is 2,000 ms, and unknown scan delay is 1,000 ms. The Python processor has separate default minimum confidence 100 (weak matches are diagnostics only and are not stored as attendance) and per-fingerprint cooldown default 10 seconds. Both settings are configurable through application settings; firmware floor/cooldown are constants.

Firmware emits status text/JSON; attendance JSON events include fingerprint `match`, `unknown`, `low_confidence`, card `card`, `card_unreadable`; card write events identify operation, UID, card type, data hex, success, verification, and result event. It also emits textual enrollment/delete/wipe/count progress consumed by the host parser. RFID supports Classic Mini/1K/4K and Type 2 variants that the detector can safely identify (Ultralight 48-byte, NTAG215, NTAG216); ambiguous 144-byte Type 2 variants are unsupported. Classic authentication/write/read behavior varies by card family and adapter; it must not be generalized to arbitrary RFID cards.

Python card payload format is 48 bytes: version byte, 12-byte nonce, then AES-GCM ciphertext+tag. Plaintext contains fingerprint ID, UTF-8 student-number length, and a padded 17-byte number; the normalized card UID is authenticated associated data. Registration writes and checks the exact payload/UID/type before binding the UID in SQLite. Attendance validates UID, decrypts payload, and checks fingerprint ID/student number/database UID linkage. Card payload encryption is separate from access control or encryption of local files.

## Workflows and failure boundaries

- **First run:** password, device, schedule, branding. Password completion is inferred from `auth`; remaining flags are persisted. Device step may be skipped. If marker exists but password record is missing, setup is recovery-required, not a password reset.
- **Connection:** candidate port ranking plus identity handshake; reader starts after connection, receives lines continuously, even in command mode. Auto-reconnect is enabled by default; saved port can fall back to discovery if stale.
- **Enrollment:** device allocates ID and captures twice; student record is saved only after successful firmware event. Student form validation/database validation are separate operations.
- **Attendance:** host event parser resolves identity and inserts event; unknown fingerprint/card events use ID 0. Repeated events can be suppressed by Python cooldown. Status presentation uses schedule and optional half-day override.
- **Fingerprint deletion:** device success event required before local deletion; old attendance becomes ID 0.
- **Device wipe:** local data clear occurs after firmware reports successful wipe; device and DB are separate stores, so partial failure can leave mismatch.
- **Backup/restore:** database-only snapshots; restore replaces live DB and does not restore firmware templates, settings, or card keys. API permission is `restore`; source validation must be checked in `database.py` when changing the implementation.
- **Backup/restore:** backup currently uses `shutil.copy2()` on the main DB file while connections use WAL mode; it does not call SQLite's backup API or explicitly checkpoint WAL. Whether a copy includes all recently committed WAL-only pages is not guaranteed by this code and is not covered by tests. Restore replaces the live DB and does not restore firmware templates, settings, or card keys. Restore is limited to resolved files under the backup directory and checks regular-file existence, `.db` suffix, minimum SQLite header size/magic before copying; it does not validate app schema or row-level integrity.
- **Exports:** CSV writer uses UTF-8 with BOM and prefixes formula-triggering strings with apostrophe; 10+-digit student numbers are forced to text. Native Save As is used when a window exists.

Do not claim DB backup includes sensor templates, settings, RFID key, or logs. Do not claim card UIDs/templates are synchronized with a restored DB. The application does not provide remote/cloud synchronization or biometric sensor backup.

The host-only suite run for this audit also exposed a stale test assumption in `tests/test_database_features.py`: it attempts to register fingerprint ID `999999` and expects a row to be cleared, but current validation rejects IDs outside 1-127. That test failed; it was not changed as part of this documentation task.

## Tests and evidence coverage

Focused active tests include:

| Area | Evidence files |
| --- | --- |
| Launcher/preflight, web UI, import boundary | `tests/test_startup_preflight.py`, `tests/test_gui_web_smoke.py`, `tests/test_active_v3_import_boundary.py` |
| Device protocol/discovery/serial concurrency | `tests/test_active_firmware_protocol.py`, `tests/test_auto_port_probe.py`, `tests/test_api_reader_thread_race.py`, `tests/test_serial_handler_host_gate.py`, `tests/test_sensor_failure_handshake_recovery.py` |
| Authentication and authorization | `tests/test_v3_authentication.py`, `tests/test_permissions_and_attendance_tagging.py`, `tests/test_database_security.py` |
| Database, reset, exports, evaluation | `tests/test_database_features.py`, `tests/test_database_reset.py`, `tests/test_attendance_export_rows.py`, `tests/test_attendance_status.py`, `tests/test_attendance_processor.py` |
| UI regressions, form validation, settings, shutdown | `tests/test_attendance_ui_regressions.py`, `tests/test_student_input_validation.py`, `tests/test_settings_persistence.py`, `tests/test_gui_shutdown.py` |
| Hardware smoke | `tests/physical_esp32_smoke.py` and tests marked `hardware`; require physical devices and are not established by host-only test runs. |

Repository test configuration sets `testpaths=tests`; markers include unit, integration, archived UI (`ui_qt`, `ui_tk`), and `hardware`. Node is needed for the JS test/check scripts. A passing unit/mock suite does not establish physical ESP32/AS608/RC522 behavior. The final docs audit should report which checks were actually run rather than assume release qualification.

## Historical and unsupported boundary

v1 is CustomTkinter and v2 is Qt/PySide. Those implementations, their UI tests, `python/gui/legacy`, `python/gui_web/v2_reference`, and old standalone firmware sketches remain for history/regression only. `firmware/ESP32_Fingerprint_AllInOne` is not the maintained DSIS firmware even though a protocol test also checks a host-gating string there. The `system/`, `Build/DSIS_v1`, and `Build/DSIS_v2` trees are not the active product source/package target. Keep historical forensic/security/regression reports as dated evidence; they do not supersede current code.

## Source evidence

Key implementation: `run_web_gui.py`, `python/startup_preflight.py`, `python/gui_web/main_web.py`, `python/gui_web/api.py`, `python/config.py`, `python/settings_store.py`, `python/core/{auth,permissions,database,serial_handler,device_discovery,commands,attendance,attendance_status,attendance_calendar,rfid_card,logger}.py`, `python/gui_web/web/`, `firmware/ESP32_DSIS_AllInOne/`, `Build/DSIS_v3.spec`, and the tests listed above. The displayed repo may contain additional archived, generated, build, asset, and local runtime files; their presence alone does not make them maintained application components.

Last reviewed: 2026-10-16.
