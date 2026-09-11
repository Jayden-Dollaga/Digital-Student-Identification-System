# DSIS v3 System Architecture

This document describes the maintained application at commit `aa457e0`. Older interfaces are documented separately in [UI lineage](../History/ui-lineage.md).

## System boundary

DSIS combines four runtime layers:

1. **Hardware**: an ESP32 WROOM-32 controller and AS608 fingerprint sensor.
2. **Python backend**: serial discovery, protocol handling, attendance processing, permissions, SQLite persistence, backups, reports, and logging.
3. **Web UI**: HTML, CSS, and JavaScript rendered in a native pywebview window.
4. **Local data**: SQLite records, JSON settings, backups, charts, exports, and timestamped logs under `data/`.

The supported launcher is `run_web_gui.py` or `run_web_gui.bat`. The application does not require a web server: pywebview loads `python/gui_web/web/index.html` into a native desktop window and exposes the Python API as `window.pywebview.api`.

## Runtime components

### Firmware

`firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino` is the maintained firmware source. It communicates with the host at 115200 baud and communicates with the AS608 sensor internally at 57600 baud. The sensor UART uses ESP32 GPIO14 for sensor TX/RX input and GPIO27 for sensor RX/TX output.

The firmware supports `ID?`, `SCAN`, `STOP`, `ENROLL`, `DELETE`, `WIPE`, `LIST`, and host-status commands. It emits JSON status and attendance events and retains text messages needed by compatibility parsers.

### Core backend

- `python/core/device_discovery.py`: enumerates and ranks ports, probes candidate ports, captures boot output, and validates DSIS identity JSON.
- `python/core/serial_handler.py`: owns the pyserial connection, buffering, command writes, disconnects, reconnects, and device metadata.
- `python/core/attendance.py`: parses JSON and compatibility text events, applies confidence and cooldown rules, and returns structured results.
- `python/core/database.py`: creates the SQLite schema, validates student data, stores attendance, reports, charts, backups, and restores.
- `python/core/permissions.py`: applies local role permissions to protected operations.
- `python/core/logger.py`: writes console and per-run log output.
- `python/config.py` and `python/settings_store.py`: provide defaults, environment overrides, and persisted operator settings.

`python/services/` contains compatibility wrappers. The active v3 API calls the core modules directly for most operations.

### Webview bridge

`python/gui_web/main_web.py` creates the native window and attaches an `Api` instance. `python/gui_web/api.py` is the only supported bridge from JavaScript to Python. Public `Api` methods return JSON-safe dictionaries, lists, strings, booleans, or numbers.

The frontend in `python/gui_web/web/app.js` calls methods such as `connect`, `disconnect`, `start_scan`, `stop_scan`, `get_students`, `get_attendance_evaluation`, `export_attendance_evaluation_csv`, `create_backup`, and `restore_backup`. The backend pushes asynchronous events back through `window.dsisEvent`, including connection status, scan results, enrollment progress, delete/wipe progress, logs, and device mode changes.

## Main application flow

1. `run_web_gui.py` adds the Python paths and calls `gui_web.main_web.main()`.
2. `main_web.py` creates the pywebview window and `Api` object.
3. `Api` creates `SerialHandler` and `AttendanceProcessor`, initializes the database, applies saved settings, attaches live logging, and starts the automatic-backup loop.
4. The web page becomes ready and loads settings, dashboard data, role state, ports, and current connection status.
5. The operator clicks **Connect**. The API asks `SerialHandler` to use the saved/manual port or auto-detect.
6. Device discovery validates the DSIS identity handshake before the connection is adopted.
7. A background reader receives complete serial lines. API parsers update the web UI through event pushes.
8. Database changes trigger page refreshes. A successful scan refreshes the current attendance evaluation window without changing its selected period.

## Connection and synchronization rules

- The host connection uses 115200 baud. The internal sensor link uses 57600 baud.
- A port is not considered connected until the device returns valid DSIS identity metadata with a supported protocol version.
- Auto-detection ranks detected ports using descriptors and known USB bridge identifiers, then probes candidates.
- A saved port can become stale when a board is moved to another USB port. Use **Forget saved port** or enable auto-discovery.
- The serial handler prevents overlapping reconnect workers and reuses an already-open matching connection rather than probing the same COM port again.
- After connection, the API requests the device fingerprint count. The count is refreshed after connection, wipe, reconnect, and relevant device operations.
- If the board disconnects during enrollment, delete, or wipe, pending UI operations are cleared and the UI returns to disconnected state.

## Enrollment flow

Enrollment is a stateful workflow:

1. The operator enters student number, name, grade, and section.
2. Live validation checks the fields before enrollment begins.
3. The frontend sends `ENROLL` to the ESP32.
4. The API forwards device progress events such as assigned ID, capture steps, success, cancellation, or failure.
5. The fingerprint ID is assigned by the device, not typed by the operator.
6. The student row is saved only after the device reports successful enrollment.
7. Cancel or disconnect returns the device to command mode and discards unsaved form state.

## Scanning and attendance

1. The operator starts scan mode.
2. The ESP32 emits a JSON match, unknown, or low-confidence event.
3. `AttendanceProcessor` parses the event and resolves the student profile.
4. The minimum confidence setting filters weak matches.
5. The cooldown prevents repeated scans for the same fingerprint from creating immediate duplicates.
6. Valid events are written to SQLite with explicit date, time, timestamp, status, and event type.
7. Unknown scans use the reserved `fingerprint_id = 0` / `Unregistered` system row.
8. The API emits `scan_result`; the frontend updates the recent activity table, dashboard counters, and the selected Attendance Evaluation view.

## Attendance evaluation

The dashboard supports day, Monday-to-Sunday week, and calendar-month windows. It counts distinct attendance dates for each student. The denominator is the number of dates on which any attendance activity was observed, so empty weekends or holidays do not automatically reduce every student's rate.

Each row includes days present, days absent, attendance rate, and one of four categories: Excellent, Good, Needs attention, or Low attendance. The frontend supports sorting by presence, rate, or name. Roles with `export` or `backup` permission can export the selected evaluation as CSV.

## Data, permissions, and destructive operations

The SQLite database is the live source for current reports. Backups are snapshots and are not used as a second history source during normal operation. Restore replaces the active database after path and file validation.

Roles are local action gating, not authentication:

- Administrator: full supported workflow permissions.
- Teacher: scan, export, and backup permissions.
- Guest: scan permission.

Device wipe and local database clearing are separate operations. A device wipe removes fingerprint templates from the ESP32; local student and attendance records are only changed by the explicit local data operation. Operators should create a backup before destructive maintenance.

## v2 reference boundary

`python/gui_web/v2_reference/` preserves the former PySide6 implementation for parity review. It is not imported by v3. The original v1 CustomTkinter and v2 Qt applications remain under `archive/legacy-ui/`.

Last reviewed: 2026-09-11, against commit `aa457e0`.
