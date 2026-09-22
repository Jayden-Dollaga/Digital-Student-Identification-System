# v3 System Architecture

This document describes the maintained v3 runtime from the executable entry point through the UI bridge, Python core, database, and hardware.

## Runtime diagram

    [AS608]
       │ UART 57600
       ▼
    [ESP32 firmware]
       │ USB serial 115200
       ▼
    [SerialHandler] ──► [AttendanceProcessor] ──► [SQLite]
           │                    │                    │
           │                    └──────────────► UI events
           │
           └──► [DeviceDiscovery]

    [index.html + app.js]
              │
              │ window.pywebview.api
              ▼
         [gui_web.api.Api]
              │
        ┌─────┼─────────────────────────────┐
        ▼     ▼             ▼               ▼
     database attendance  permissions      auth
        │                    │               │
        └──────────────► settings_store ◄───┘

## Startup and launch

The maintained launcher is `run_web_gui.py`. It adds `python/` and `python/gui_web/` to the import path and calls `gui_web.main_web.main()`.

`main_web.py`:

1. installs uncaught-exception hooks,
2. creates `Api()`,
3. loads `python/gui_web/web/index.html`,
4. creates a pywebview window at 1180×740 with a minimum 900×600 size,
5. exposes `Api` as the JavaScript API,
6. attaches the close handler,
7. starts the native webview loop.

Closing the window calls `Api.disconnect()`.

## UI layer

The v3 UI is contained in:

- `python/gui_web/web/index.html`
- `python/gui_web/web/app.js`
- `python/gui_web/web/styles.css`

Pages currently present:

- Dashboard
- Attendance
- Students
- Reports
- Logs
- Settings
- Calendar

The page contains setup/auth/calendar modals in addition to the main pages.

The frontend is not a server application. It runs inside the native pywebview window and calls Python directly through `window.pywebview.api`.

## Bridge layer

`python/gui_web/api.py` is the integration boundary. It:

- validates UI input,
- checks permissions,
- controls serial operations,
- calls database/report/calendar helpers,
- persists settings,
- manages authentication/session state,
- converts backend outcomes into JSON-compatible dictionaries,
- pushes live events back into JavaScript with `window.dsisEvent(...)`.

See [pywebview-bridge.md](pywebview-bridge.md) for the complete public method contract.

## Core runtime modules

| Module | Responsibility |
| --- | --- |
| `core.auth` | Password hashing, verification, first-password creation |
| `core.permissions` | In-memory session role, role hierarchy, permission checks |
| `core.database` | SQLite schema, student/attendance CRUD, reports, backup/restore |
| `core.attendance` | Parse device events, confidence classification, cooldown |
| `core.attendance_status` | Convert scan time + schedule into attendance status |
| `core.attendance_calendar` | Holidays, suspensions, half-days, recurring weekday exclusions |
| `core.serial_handler` | COM connection, reading, command sending, auto-reconnect |
| `core.device_discovery` | Port ranking and `ID?` handshake |
| `core.commands` | High-level ESP32 command wrappers |
| `core.firmware_helper` | Firmware candidate discovery and upload support |
| `core.logger` | Console/file/UI logging |
| `core.setup_wizard` | First-run step routing |
| `core.utils` | JSON/date/export helper functions |

The two active modules under `python/services/` are thin wrappers around database functions and preserve service-oriented interfaces used by older code.

## Serial boundary

The two serial rates must not be conflated:

- **PC ↔ ESP32:** 115200 baud
- **ESP32 ↔ AS608:** 57600 baud

The PC never talks directly to the AS608. The ESP32 owns the AS608 UART and translates its fingerprint operations into host-visible serial output.

## Device discovery and handshake

`device_discovery.py` enumerates candidate COM ports and probes them at the selected host baud. A supported device must answer with JSON containing:

- `device`: `Digital Student Identification System`
- `protocol`: integer version at least 1

The firmware also emits the same identity JSON during boot. Discovery can therefore recognize a device from buffered boot output even when the device does not reach a later `ID?` response phase.

The probe disables DTR/RTS before opening the port to avoid an unintended ESP32 reset.

## Serial read loop

After connection, `Api._start_read_loop()` creates the background serial-reader thread. It reads complete newline-delimited lines from `SerialHandler.read_line()`.

The API parser classifies input into:

- scan results,
- enrollment progress,
- delete progress,
- wipe progress,
- fingerprint counts,
- connection/device state,
- log/diagnostic text.

The frontend receives push events without polling the serial port itself.

## Attendance flow

1. Firmware enters scan mode.
2. AS608 finds a fingerprint.
3. Firmware emits a JSON attendance event.
4. Python parses the event.
5. Python applies the desktop confidence threshold and per-ID cooldown.
6. Successful events are written to SQLite.
7. `event_type` is assigned as `time_in` for the first scan of that fingerprint on that date and `time_out` for later scans.
8. The API pushes `scan_result` and data refresh events to the UI.

Firmware and desktop filtering are separate. Firmware accepts matches at its floor of 50 confidence; the default Python classification threshold is 100. Therefore a firmware-accepted match with confidence 50–99 is stored as `WEAK MATCH` by the desktop processor.

## Enrollment flow

The frontend starts an enrollment request through `Api.start_enroll()`. The firmware:

1. selects the next free ID when none is supplied,
2. otherwise validates an explicit ID in the 1–127 range,
3. captures the same finger twice,
4. creates a model,
5. stores the template in the AS608.

The successful device message is observed by the bridge. Student metadata is persisted through `Api.save_student()` only after the device-side enrollment succeeds.

Re-enrollment can migrate an existing student record to a new fingerprint ID while updating historical attendance references.

## Delete and wipe

Delete and wipe have two domains:

- device template state,
- local database state.

A normal delete of a student is device-first: the active UI requests device deletion and only successful device deletion should be followed by local student cleanup.

A device wipe reports progress back to Python. On the success message, Python clears local attendance/student data through `db.clear_all_data()` and refreshes the device fingerprint count.

`wipe_all_data()` is the explicit local-data destructive operation and requires the wipe permission.

## Persistence

The live SQLite database is `data/attendance.db`. Settings live in `data/settings.json`. Backups, logs, exports, and charts are separate filesystem outputs.

SQLite enables foreign-key enforcement for the attendance-to-student relationship.

## Authentication and permissions

The active role is held in process memory. The role stored under `settings.json` is display continuity only and is not an authorization source.

The default session is Guest. Password-authenticated roles expire after 600 seconds of inactivity by default. `touch_session()` extends an active session.

The backend permission checks are authoritative; frontend button hiding is convenience only.

## Background threads

| Activity | Thread/context |
| --- | --- |
| Serial read loop | daemon reader thread started after connection |
| Auto reconnect | `SerialHandlerReconnect` daemon thread |
| Automatic backup | API background thread started after the pywebview window is attached |
| UI log handler | logging callback path feeding the window |
| Main webview | native/UI thread |

The backup worker deliberately starts after `set_window()` so it does not compete with GUI creation during startup.

## Shutdown

When the pywebview window closes:

1. `Api.disconnect()` is called.
2. Reconnect activity is stopped.
3. The serial device receives `HOST_DISCONNECTED` status text where possible.
4. The device receives `STOP`.
5. The serial handle is closed.

Unhandled main-thread and worker exceptions are written through the centralized logger.
