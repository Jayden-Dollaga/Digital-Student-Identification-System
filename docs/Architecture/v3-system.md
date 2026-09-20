# DSIS v3 System Architecture

This is the implementation-level reference for the maintained DSIS v3 application. It describes runtime boundaries, component responsibilities, synchronization rules, data flow, permissions, and destructive operations.

## System boundary

DSIS v3 combines ESP32 firmware, an AS608 fingerprint sensor, a Python backend, an HTML/CSS/JavaScript frontend rendered by pywebview, and SQLite/JSON local storage.

The supported launchers are `run_web_gui.py` and `run_web_gui.bat`. No application web server is required.

## Current hardware and protocol

| Property | Value |
| --- | --- |
| Device | Digital Student Identification System |
| Board | ESP32 |
| Firmware | 1.0.10 |
| Sensor | AS608 |
| Protocol | 1 |
| Host serial | 115200 baud |
| Sensor UART | 57600 baud |
| AS608 TX -> ESP32 | GPIO14 |
| AS608 RX -> ESP32 | GPIO27 |

## Runtime components

- `python/gui_web/main_web.py` — native pywebview window lifecycle and shutdown handling.
- `python/gui_web/api.py` — JavaScript-to-Python bridge.
- `python/core/device_discovery.py` — COM-port ranking and DSIS identity handshake.
- `python/core/serial_handler.py` — live serial connection, buffering, reconnect, and device metadata.
- `python/core/attendance.py` — scan parsing, cooldown, confidence classification, and attendance recording.
- `python/core/attendance_status.py` — time-based attendance status.
- `python/core/attendance_calendar.py` — holiday, suspension, and half-day schedule exceptions.
- `python/core/database.py` — SQLite schema, migration, records, reports, backups, restore, exports.
- `python/core/auth.py` — password creation and PBKDF2-HMAC-SHA256 verification.
- `python/core/permissions.py` — in-memory role sessions and backend authorization.
- `python/core/logger.py` — structured console and file logging.

`python/services/` contains compatibility wrappers; the active v3 API uses the core modules for most current workflows.

## Webview bridge

The frontend communicates with Python through `window.pywebview.api`. Python pushes asynchronous events through `window.dsisEvent(event, payload)`.

Current event families include `scan_result`, `serial_line`, `log_line`, `enroll_progress`, `delete_progress`, `wipe_progress`, `fingerprint_count`, `connection_status`, `connection_changed`, `connection_troubleshooting`, `serial_error`, `data_changed`, and `mode_changed`.

## Device discovery

The discovery layer sends `ID?` to candidate COM ports at 115200 baud and validates the DSIS device identifier plus a supported protocol version. The handshake timeout is 3 seconds.

A saved COM port is treated as a preference. If Windows no longer exposes that port, DSIS can fall back to discovery.

## Main runtime flow

```text
launcher -> pywebview -> Api initialization -> first-run setup -> device discovery -> serial reader -> workflow -> SQLite/API event -> UI refresh
```

## Enrollment

Student information is validated before enrollment. `ENROLL` selects the next free fingerprint slot; `ENROLL:<id>` requests an explicit ID from 1-127.

The ESP32/AS608 captures the finger twice, creates the model, stores it, and reports success. The local student row is saved only after successful device storage.

Disconnect or cancellation clears the pending operation and returns the device toward command mode.

## Attendance scanning

The firmware emits structured or compatibility events after fingerprint matching. The Python processor applies an application cooldown and confidence classification before database recording.

The firmware hardware match floor is 50. The Python default classification threshold is 100.

| Confidence | Application status | Stored? |
| ---: | --- | --- |
| >= 100 | GOOD MATCH | Yes |
| 50-99 | WEAK MATCH | Yes |
| < 50 | No match event | No |

A WEAK MATCH is still stored by the current processor; 100 is not a second rejection gate.

Duplicate protection is layered: firmware has an approximately 2-second post-scan delay and the application cooldown defaults to 10 seconds per fingerprint.

Unknown scans use fingerprint ID 0 and the permanent `Unregistered` database row.

## Attendance status and calendar

Default schedule values are 08:00 time-in, 17:00 time-out, 15-minute early threshold, 15-minute late threshold, and 0-minute absent threshold.

Supported calendar exception types are `holiday`, `suspension`, and `half_day`. Half-day entries may override time-in/time-out.

## Attendance evaluation

Evaluation supports Day, Monday-Sunday Week, and Calendar Month. Distinct attendance dates are counted per student.

The denominator is based on dates with attendance activity in the selected period. Empty dates are not automatically counted as school days by this evaluation.

| Rate | Category |
| ---: | --- |
| 90-100% | Excellent |
| 75-89% | Good |
| 50-74% | Needs attention |
| below 50% | Low attendance |

Evaluation viewing uses `attendance_evaluation`; CSV export uses `export`.

## Delete and wipe

### Delete

The v3 workflow sends physical `DELETE:<id>` first and removes the linked local student profile only after device success. Hardware failure leaves the local profile intact.

### Wipe

`WIPE` is destructive. After device success, the v3 API clears linked local student/attendance data and refreshes the fingerprint count. If local cleanup fails after hardware success, the API reports that partial state.

Create a backup before destructive maintenance.

## Persistence

| Location | Purpose |
| --- | --- |
| `data/attendance.db` | Live SQLite database |
| `data/settings.json` | Preferences, setup state, authentication record |
| `data/backups/` | Timestamped database snapshots |
| `data/logs/` | Per-run logs |
| `data/charts/` | Generated charts |
| `data/exports/` | Generated reports/CSV |

## Roles and authentication

| Role | Permissions |
| --- | --- |
| Administrator | scan, enroll, delete, wipe, export, backup, restore, attendance evaluation, calendar management |
| Teacher | scan, export, backup, attendance evaluation |
| Guest | scan, attendance evaluation |

Non-guest sessions expire after 600 seconds of inactivity by default. The persisted `current_role` value is not trusted for authorization.

There is no built-in default administrator password. First-run passwords require at least 8 characters and are stored using PBKDF2-HMAC-SHA256 with a 16-byte random salt and 310,000 iterations.

## Failure handling

Current v3 behavior includes stale-port recovery, identity-validated discovery, automatic reconnect, serial buffering, operation-state cleanup after disconnect, console fallback when file logging fails, backup/restore validation, and permission checks in the backend.

## Legacy boundary

v1 and v2 UI implementations are preserved under `archive/legacy-ui/`; `python/gui_web/v2_reference/` is reference-only; `tests/Prototype/` contains isolated visual prototypes. None is the supported v3 launcher.

Last reviewed: 2026-09-20.