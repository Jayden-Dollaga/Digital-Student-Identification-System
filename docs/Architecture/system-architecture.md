# DSIS v3 System Architecture

This is the technical architecture reference for the maintained DSIS v3 implementation.

## System boundary

DSIS is a local-first Windows application made of five cooperating parts:
1. ESP32 firmware
2. AS608 fingerprint sensor
3. Python backend
4. HTML/CSS/JavaScript frontend rendered in a native pywebview window
5. SQLite and JSON local storage

No application web server is required.

## Runtime components

### Launcher

`run_web_gui.py` prepares the runtime import paths and delegates to the active web GUI. `run_web_gui.bat` is the Windows convenience launcher.

### Native application shell

`python/gui_web/main_web.py` creates the pywebview window, attaches the `Api`, installs exception hooks, and disconnects the hardware when the window closes.

The active HTML interface is loaded from `python/gui_web/web/index.html`. JavaScript communicates with Python through `window.pywebview.api`.

### Python API bridge

`python/gui_web/api.py` is the supported bridge for setup, session state, serial operations, students, attendance, reports, settings, calendar management, backup/restore, logging, and exports.

The backend pushes asynchronous changes to the frontend through `window.dsisEvent(event, payload)`.

### Device discovery

`python/core/device_discovery.py` enumerates COM ports, scores likely candidates using descriptions and known USB VID:PID values, sends `ID?`, and validates the DSIS identifier and supported protocol version.

| Property | Current value |
| --- | --- |
| Device identifier | Digital Student Identification System |
| Minimum protocol | 1 |
| Handshake | `ID?` |
| Host baud | 115200 |
| Handshake timeout | 3 seconds |

### Serial handler

`python/core/serial_handler.py` owns the live pyserial connection, buffered reads, command writes, metadata, disconnect handling, stale-port recovery, and automatic reconnect.

### Attendance processor

`python/core/attendance.py` parses structured JSON and compatibility text, applies the application cooldown, classifies confidence, looks up students, and records attendance.

### Attendance status and calendar

`python/core/attendance_status.py` evaluates time-based attendance state. `python/core/attendance_calendar.py` resolves date-specific schedule exceptions. Supported exception types are `holiday`, `suspension`, and `half_day`.

### Database

`python/core/database.py` owns SQLite initialization, schema migration, student and attendance records, reporting helpers, charts, backups, restore validation, and exports.

### Authentication and permissions

`python/core/auth.py` implements first-run password creation and PBKDF2-HMAC-SHA256 verification. `python/core/permissions.py` holds the effective role in memory and fails closed for unknown roles.

The persisted `current_role` setting is for UI continuity and is not used as the authorization source.

## Architecture diagram

```text
                         Operator
                            |
                            v
                 +-----------------------+
                 |     DSIS v3 Web UI    |
                 | HTML / CSS / JS       |
                 +-----------+-----------+
                             |
                   window.pywebview.api
                             |
                             v
                 +-----------------------+
                 |      Python API       |
                 | python/gui_web/api.py |
                 +-----+------------+----+
                       |            |
                       |            +------> SQLite / JSON / backups / logs
                       |
                       v
                +--------------+
                | Core modules |
                | discovery    |
                | serial       |
                | attendance   |
                | auth/roles   |
                | calendar     |
                | database     |
                +------+-------+
                       |
                 USB Serial 115200
                       |
                       v
                    +------+
                    | ESP32 |
                    +--+---+
                       |
                 UART2 57600
                       |
                       v
                    +------+
                    | AS608|
                    +------+
```

## Host protocol

The PC-to-ESP32 connection is a newline-delimited serial protocol at **115200 baud**.

Current firmware commands:
```text
ID?
SCAN
STOP
LIST
ENROLL
ENROLL:<id>
DELETE:<id>
WIPE
STATUS:<state>
```

The maintained firmware also emits structured JSON attendance events.

### Match event
```json
{"type":"attendance","event":"match","id":1,"confidence":223}
```

### Unknown event
```json
{"type":"attendance","event":"unknown"}
```

### Low-confidence event
```json
{"type":"attendance","event":"low_confidence","confidence":42}
```

## Data flow

### Enrollment
```text
Student form -> validation -> ENROLL -> ESP32/AS608 capture -> model -> store -> success -> SQLite student row
```

The local student profile is saved only after the device confirms successful template storage.

### Attendance
```text
Finger -> AS608 -> ESP32 match -> serial event -> AttendanceProcessor -> cooldown/classification -> SQLite -> API event -> UI refresh
```

### Deletion

The v3 workflow sends the physical delete command first and removes the linked local profile only after confirmed device success.

### Wipe

`WIPE` is destructive. The v3 workflow waits for successful device template deletion, then clears linked local student/attendance data and refreshes the device count. A local cleanup failure after device success is reported as a partial result.

## Persistent state

| Location | Purpose |
| --- | --- |
| `data/attendance.db` | Student and attendance database |
| `data/settings.json` | Preferences, setup state, authentication record |
| `data/backups/` | Timestamped database snapshots |
| `data/logs/` | Per-run operational logs |
| `data/charts/` | Generated chart images |
| `data/exports/` | Generated report/CSV files |

## Roles

| Role | Permissions |
| --- | --- |
| Administrator | scan, enroll, delete, wipe, export, backup, restore, attendance evaluation, calendar management |
| Teacher | scan, export, backup, attendance evaluation |
| Guest | scan, attendance evaluation |

Authenticated non-guest sessions expire after 600 seconds of inactivity by default.

## Failure and recovery

The design explicitly handles stale ports, serial disconnects, automatic reconnect, malformed/legacy serial lines, log-file failures, operation cancellation, and database backups before destructive maintenance.

## Security boundary

DSIS does not claim encryption at rest or regulatory compliance. Production deployments should protect the Windows host and runtime files, especially the SQLite database, settings, backups, and logs.

## Legacy boundary

Historical implementations remain under `archive/legacy-ui/` and `python/gui_web/v2_reference/`. UI prototypes under `tests/Prototype/` are isolated previews and are not the supported v3 runtime.

Last reviewed: 2026-09-20.