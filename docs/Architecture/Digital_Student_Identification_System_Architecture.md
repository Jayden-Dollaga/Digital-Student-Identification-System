# Digital Student Identification System Architecture

This document describes the maintained DSIS v3 system: a Windows desktop application, a local Python backend, an ESP32 attendance device, and local data stores. Historical v1/v2 interfaces and prototypes are called out only to clarify the active boundary.

## Static Architecture

```text
Digital Student Identification System (DSIS)
|
+-- PEOPLE AND OPERATIONS
|   +-- Administrator
|   |   +-- First-run password setup and privileged configuration
|   |   +-- Student enrollment, device deletion, wipe, restore, backup
|   |   +-- Calendar, attendance rules, settings, and user administration
|   +-- Teacher
|   |   +-- Attendance review, reports, export, and backup
|   +-- Guest
|       +-- Scan and attendance evaluation access
|
+-- DESKTOP SOFTWARE (Windows, local process)
|   +-- Supported launchers
|   |   +-- run_web_gui.py
|   |   +-- run_web_gui.bat
|   |   +-- python/gui_web/main_web.py
|   |       +-- Loads configuration and creates the Api object
|   |       +-- Creates native pywebview window
|   |       +-- Loads python/gui_web/web/index.html from disk
|   |       +-- Closes serial connection when the window exits
|   +-- Web presentation layer
|   |   +-- python/gui_web/web/index.html
|   |   +-- python/gui_web/web/styles.css
|   |   +-- python/gui_web/web/app.js
|   |   +-- Screens: Dashboard, Attendance, Students, Reports, Logs, Settings
|   |   +-- First-run setup wizard and device/setup dialogs
|   |   +-- Presentation and interaction only; not an authorization boundary
|   +-- In-process JavaScript/Python bridge
|   |   +-- JavaScript calls window.pywebview.api.<method>(...)
|   |   +-- Python pushes window.dsisEvent(event, payload)
|   |   +-- JSON-compatible dictionaries, lists, booleans, and scalar results
|   +-- python/gui_web/api.py : Api orchestration boundary
|   |   +-- Frontend operations: connect, disconnect, scan, enroll, student CRUD
|   |   +-- RFID registration, card erase, delete, wipe, reports, exports
|   |   +-- Permission checks and operation-state coordination
|   |   +-- Serial read thread and line-to-event parsing
|   |   +-- AttendanceProcessor integration and UI event delivery
|   |   +-- Background device monitoring and automatic backup work
|   +-- Python domain and infrastructure (python/core)
|       +-- device_discovery.py : COM enumeration, ID? identity handshake
|       +-- serial_handler.py : serial lifecycle, buffering, reconnect, metadata
|       +-- commands.py : command construction and device operation support
|       +-- attendance.py : ScanOutcome and AttendanceProcessor
|       +-- attendance_status.py : time-in, time-out, late/early status rules
|       +-- attendance_calendar.py : holidays, suspensions, half-day overrides
|       +-- database.py : SQLite schema, validation, migrations, queries
|       +-- auth.py : first password setup, salted PBKDF2 hash and verification
|       +-- permissions.py : guest/teacher/admin in-memory session and checks
|       +-- rfid_card.py : RFID payload encryption/decryption and UID handling
|       +-- setup_wizard.py : persisted first-run state
|       +-- logger.py : structured application and serial diagnostics
|       +-- firmware_helper.py and utils.py : supporting utilities
|       +-- config.py and settings_store.py : defaults and JSON preferences
|       +-- python/services : compatibility wrappers; not the primary v3 API path
|
+-- USB SERIAL AND DEVICE PROTOCOL
|   +-- Windows COM port at 115200 baud
|   +-- Discovery probe: ID?; validate DSIS identity and supported protocol
|   +-- Commands include ID?, ENROLL, ENROLL:<id>, DELETE:<id>, WIPE, LIST,
|   |   SCAN, and STOP; command/scan mode is coordinated by the host and device
|   +-- Device status and attendance are emitted as newline-delimited serial text
|   |   +-- JSON status: {"type":"status","state":"SCAN_MODE|CMD_MODE"}
|   |   +-- JSON match: {"type":"attendance","event":"match","id":N,
|   |   |                 "confidence":N}
|   |   +-- JSON unknown/low_confidence attendance events
|   |   +-- JSON card/card_unreadable attendance events with UID and card data
|   |   +-- Progress and compatibility text parsed by the Python Api
|
+-- HARDWARE (ESP32 all-in-one firmware)
|   +-- firmware/ESP32_DSIS_AllInOne/ESP32_DSIS_AllInOne.ino
|   |   +-- Owns sensor interaction, enrollment, matching, and device modes
|   |   +-- Reports identity, protocol, status, progress, and scan results
|   |   +-- Host UART: USB serial at 115200 baud
|   |   +-- Sensor UART: AS608 at 57600 baud
|   |   +-- Fingerprint UART pins: ESP32 GPIO14 (sensor TX), GPIO27 (sensor RX)
|   |   +-- GPIO2 status LED; firmware scan cooldown is about 2 seconds
|   +-- AS608 fingerprint module
|   |   +-- Captures finger images and creates/stores biometric templates
|   |   +-- Matches scans and reports template ID and confidence
|   |   +-- Templates live on the sensor, not in SQLite or a database backup
|   +-- RC522 RFID reader
|   |   +-- SPI: SCK GPIO18, MISO GPIO19, MOSI GPIO23
|   |   +-- SDA/SS GPIO5, reset GPIO4
|   |   +-- Reads card UID and supported card payloads; supports card workflows
|   +-- ESP32 feedback and mode state
|       +-- LED feedback for ready, scan, enrollment, success, and error states
|       +-- Command mode handles management; scan mode handles attendance reads
|
+-- LOCAL DATA AND OUTPUTS
|   +-- data/attendance.db : authoritative local SQLite database
|   |   +-- students: fingerprint_id, student_no, student_name, grade, section,
|   |   |             card_uid, enrollment_date, updated_date
|   |   +-- attendance: id, fingerprint_id, date, time, confidence, status,
|   |   |               timestamp, event_type
|   |   +-- fingerprint_id 0: permanent Unregistered row for unknown scans
|   |   +-- Foreign key from attendance.fingerprint_id to students.fingerprint_id
|   +-- data/settings.json : settings, setup state, auth hash/salt, RFID app key
|   +-- data/backups/ : timestamped SQLite snapshots; no sensor templates
|   +-- data/logs/ : runtime logs
|   +-- data/exports/ : generated CSV and report outputs
|   +-- data/charts/ : generated chart outputs
|   +-- CSV and report APIs read local database state and write selected outputs
|
+-- DELIVERY, TESTING, AND NON-ACTIVE HISTORY
    +-- run_web_gui.py / run_web_gui.bat : supported v3 entry points
    +-- Build specs and assets support Windows packaging and application branding
    +-- tests/ : protocol, attendance, database, UI, and workflow regression checks
    +-- archive/legacy-ui/ : v1/v2 interface lineage, not the supported launcher
    +-- python/gui_web/v2_reference/ and prototypes : reference-only material
    +-- No hosted web server, cloud database, or network synchronization is required
```

## Runtime, Event, and Data Flow

The following flow is an operational view, not a second component inventory. Each path starts from a user or device event and ends with durable local state and/or a UI update.

```text
DSIS runtime event flow
|
+-- APPLICATION STARTUP
|   +-- User launches run_web_gui.py or run_web_gui.bat
|   +-- main_web.py loads settings, logger, Api, and SQLite schema
|   +-- Api initializes SerialHandler, AttendanceProcessor, and guest session
|   +-- pywebview opens web/index.html; no separate HTTP server is started
|   +-- app.js calls window.pywebview.api for initial data and UI state
|   +-- Api returns JSON-compatible values to the requesting UI component
|
+-- DEVICE CONNECTION AND SCAN
|   +-- UI requests connect or automatic discovery
|   +-- device_discovery enumerates candidate COM ports and sends ID?
|   +-- ESP32 replies with identity and protocol metadata
|   +-- serial_handler validates device, opens the port, buffers lines,
|   |   synchronizes connection state, and applies reconnect policy
|   +-- Api pushes connection_status / connection_changed to the UI
|   +-- User starts attendance; Api checks operation conflicts and sends SCAN
|   +-- ESP32 enters scan mode and polls AS608 and RC522
|   +-- AS608 match, unknown finger, or RC522 card produces a serial event
|   +-- Api serial reader parses the line and calls AttendanceProcessor
|   +-- Processor resolves fingerprint ID or card identity against SQLite
|   |   +-- Fingerprint confidence is classified by application policy
|   |   +-- Card payload can be authenticated/decrypted and linked to a student
|   |   +-- Unknown identity uses reserved fingerprint_id 0
|   |   +-- Per-fingerprint application cooldown suppresses duplicate writes
|   +-- Accepted event is stored in attendance with status and timestamp
|   +-- Api pushes scan_result and data_changed for UI refresh
|   +-- UI refreshes attendance, dashboard, recent activity, or reports
|
+-- STUDENT AND FINGERPRINT ENROLLMENT
|   +-- Admin enters student fields and chooses next or explicit sensor ID
|   +-- Api enforces backend permission and validates student data
|   +-- Host switches device to command mode and sends ENROLL or ENROLL:<id>
|   +-- ESP32/AS608 prompts for two finger captures and stores the template
|   +-- Serial progress is parsed into enroll_progress events for the dialog
|   +-- On confirmed device success, Api saves the student row to SQLite
|   +-- Student list/count refresh events update the frontend
|   +-- On failure/cancel, pending state is cleared; no successful enrollment
|       is represented as a durable student record
|
+-- RFID REGISTRATION AND ATTENDANCE
|   +-- Admin starts a registration/write workflow for a selected student
|   +-- Python creates a versioned AES-GCM payload bound to the normalized UID
|   +-- Api sends the appropriate card workflow to the ESP32/RC522
|   +-- Device reads/writes and verifies supported card data, then reports result
|   +-- Api binds the UID to the student row when registration succeeds
|   +-- During scan, firmware reports card UID, card type, and data_hex
|   +-- AttendanceProcessor resolves the encrypted DSIS payload or linked UID
|   +-- Recognized card follows the normal cooldown, attendance write, and UI path
|   +-- Unreadable or unrecognized cards produce a result without false identity
|
+-- DELETE AND WIPE
|   +-- Admin requests DELETE:<id> or WIPE through the UI
|   +-- Api enforces permission and serializes against conflicting operations
|   +-- Firmware removes the sensor template and reports success/failure
|   +-- Delete: local student is removed only after device success; historical
|   |   attendance is retained and reassigned to fingerprint_id 0
|   +-- Wipe: local linked student/attendance data is cleared only after device
|   |   success; partial failure is surfaced rather than treated as atomic
|   +-- Api pushes progress, fingerprint_count, data_changed, and connection
|       state as applicable; UI reloads affected views
|
+-- AUTHORIZATION, REPORTS, AND PERSISTENCE
|   +-- First run stores a salted PBKDF2-HMAC-SHA256 admin password record
|   +-- Login establishes an in-memory guest/teacher/admin role session
|   +-- Api checks permissions for privileged backend operations; UI hiding a
|   |   button is not authorization
|   +-- UI requests dashboard, attendance, student, calendar, and report data
|   +-- Api/core queries SQLite and applies calendar/time/status rules
|   +-- CSV export, backup, restore, and settings operations check permissions
|   +-- Backups copy SQLite only; restored data must be reconciled with hardware
|   +-- Structured logs and frontend event stream report success/failure
|
+-- PYTHON TO JAVASCRIPT EVENT DELIVERY
    +-- Api._push(event, payload) schedules window.dsisEvent(event, payload)
    +-- app.js dispatches event families to the relevant views/dialogs
    +-- Events include scan_result, serial_line, log_line, enroll_progress,
    |   delete_progress, wipe_progress, fingerprint_count, connection_status,
    |   connection_changed, connection_troubleshooting, serial_error,
    |   data_changed, mode_changed
    +-- The UI consumes pushed state rather than assuming synchronous hardware
        completion or polling every operation
```

## Component Responsibilities

| Component | Responsibility |
| --- | --- |
| `main_web.py` | Starts the native pywebview process, constructs `Api`, loads local frontend assets, and closes device I/O on shutdown. |
| `app.js`, `index.html`, `styles.css` | Render the v3 interface, collect user input, call the Python bridge, and process pushed events. |
| `Api` | Orchestrates UI use cases, authorization, serial operations, event parsing, and UI notifications. It is a local bridge, not a standalone HTTP API. |
| `device_discovery.py` / `serial_handler.py` | Find the ESP32 by identity, manage serial connection and buffering, and support status/reconnect behavior. A saved COM port is a preference, not proof of device identity. |
| `AttendanceProcessor` | Converts firmware output into a `ScanOutcome`, resolves the student, applies confidence and cooldown rules, and records eligible events. |
| Attendance status/calendar modules | Apply time-in/time-out, late/early, holiday, suspension, and half-day rules after a scan; the sensor does not make these school policy decisions. |
| `database.py` | Owns SQLite initialization, migrations, validation, student and attendance persistence, reporting queries, backups, restores, and exports. |
| `auth.py` / `permissions.py` | Verify passwords and enforce session role capabilities at the backend operation boundary. |
| `rfid_card.py` | Creates and validates versioned AES-GCM card payloads; payload authentication is associated with the normalized card UID. |
| ESP32 firmware | Owns the hardware state machine, sensor/card interactions, serial command handling, and device-originated events. It does not own student names or attendance history. |

## Data, APIs, and Contracts

### Bridge and serial APIs

The frontend calls Python methods through `window.pywebview.api`. Representative `Api` operations include `list_ports`, `connect`, `disconnect`, `start_scan`, `stop_scan`, `start_enroll`, `cancel_enroll`, `save_student`, `delete_student`, `delete_on_device`, `wipe_all_on_device`, `get_attendance`, `get_students`, `get_dashboard_stats`, `create_backup`, and CSV export methods. These are Python bridge methods, not REST endpoints.

Python pushes device and workflow changes through `window.dsisEvent(event, payload)`. Common event names are listed in the runtime diagram. Device-to-host serial messages are newline-delimited JSON for structured events, with compatibility text still parsed for status and progress. Discovery sends `ID?` at 115200 baud and validates the DSIS identifier and supported protocol.

### Attendance records

`AttendanceProcessor` returns a `ScanOutcome` containing `fingerprint_id`, `confidence`, `status`, `timestamp`, `logged`, optional `reason`, and optional RFID `method`, `uid`, `data`, and `card_type`. Confidence handling has two layers: the firmware match floor is 50; the Python default classification threshold is 100. Scores at or above the application threshold are `GOOD MATCH`; accepted matches below it are `WEAK MATCH`; the firmware does not emit a match below its floor. Weak matches are still recorded by the current processor. A default 10-second per-ID Python cooldown complements the firmware's roughly 2-second post-scan delay.

Unknown fingerprint scans use ID 0 and the permanent `Unregistered` student row so the attendance foreign key remains valid. Attendance rows store confidence, status, event timestamp, date/time fields, and `event_type` when assigned. The first event for a student/date is tagged `time_in`; later events that date are tagged `time_out` by the migration and event rules.

### Persistence

SQLite at `data/attendance.db` is authoritative for student metadata and attendance. Student template IDs are normally 1 through 127; ID 0 is reserved. `students.fingerprint_id` is the local link to the AS608 template. The attendance foreign key references this ID. Student deletion preserves history by reassigning retained attendance to ID 0.

`data/settings.json` stores user preferences and setup/authentication material, including a 16-byte random password salt and PBKDF2-HMAC-SHA256 hash at 310,000 iterations. The RFID application AES-GCM key is also persisted in settings. RFID payloads use a 12-byte nonce, version marker, authentication tag, and UID-bound associated data. A database backup does not contain that key unless settings are separately preserved, and does not contain physical sensor templates.

## Security, Performance, and Design Decisions

- The application is local-first and does not require a web server, cloud service, or network synchronization.
- The pywebview bridge is a process boundary, not a security boundary. Authorization is checked in Python for privileged actions; frontend visibility alone is insufficient.
- Roles are held in an in-memory session and privileged sessions expire after the configured inactivity timeout (600 seconds by default). A persisted role display value is not trusted for authorization.
- There is no built-in administrator password. First-run credentials are validated, salted, and hashed; password verification uses constant-time digest comparison.
- Student records and attendance in SQLite are not encrypted at rest. Restrict access to the Windows account and data directory; do not commit real student data or runtime databases.
- Sensor templates remain on the AS608 and are not included in SQLite backups. Database restore and hardware state therefore require operational reconciliation.
- RFID payloads use AES-GCM authenticated encryption. The encryption key is local application state in `settings.json`; protect that file and backups containing it.
- Device discovery checks identity and protocol instead of trusting a COM port name. A stale saved port may fall back to discovery.
- Serial reads, device monitoring, and recurring backups run outside direct UI event handling. The UI receives pushed events so long hardware operations can report progress without blocking on synchronous completion.
- Destructive delete and wipe are coordinated host/device workflows. Local cleanup follows confirmed hardware success; a wipe can still have a partial outcome if local cleanup fails after the device has been erased.
- Attendance evaluation is based on dates with attendance activity in the selected period; empty dates are not automatically treated as school days.

## Active Boundary and Limitations

The supported launch path is the v3 HTML/pywebview interface. Archived v1 CustomTkinter and v2 Qt interfaces, reference UI material, and prototypes are not active runtime components. The system is not a multi-device synchronization service, does not back up biometric templates, and does not encrypt the SQLite database at rest. Hardware behavior depends on the connected ESP32, AS608, RC522, serial drivers, and their supported firmware protocol.
