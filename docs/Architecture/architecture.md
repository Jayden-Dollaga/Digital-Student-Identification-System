# DSIS Architecture Overview

This document gives the architectural model of the maintained DSIS v3 application. For implementation-level details, see [v3 System Architecture](v3-system.md).

## Runtime layers

DSIS is a local Windows application composed of hardware, communication, application, presentation, and persistence responsibilities.

```text
┌────────────────────────────────────────────┐
│                Operator                   │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│          DSIS v3 Web Interface             │
│        HTML + CSS + JavaScript             │
└──────────────────────┬─────────────────────┘
                       │ pywebview bridge
                       │ window.pywebview.api
                       ▼
┌────────────────────────────────────────────┐
│             Python Application             │
│                                            │
│ Device Discovery · Serial Handler          │
│ Attendance · Permissions · Settings       │
│ Reports · Backup · Logging                 │
└──────────────┬─────────────────────┬───────┘
               │                     │
               │ USB Serial          │ local filesystem
               │ 115200 baud         │
               ▼                     ▼
        ┌──────────────┐       ┌──────────────┐
        │    ESP32     │       │ SQLite / JSON │
        └──────┬───────┘       │ logs/exports  │
               │ 57600 baud    └──────────────┘
               ▼
        ┌──────────────┐
        │     AS608    │
        │ fingerprint  │
        └──────────────┘
```

## Layer responsibilities

### Firmware

The maintained firmware at `firmware/ESP32_DSIS_AllInOne/ESP32_DSIS_AllInOne.ino`:

- initializes the ESP32 host serial port at 115200 baud
- initializes the AS608 UART at 57600 baud
- validates the fingerprint sensor during boot
- exposes device identity metadata
- manages command mode and scan mode
- performs enrollment, matching, deletion, listing, and wipe operations
- emits human-readable compatibility messages and structured JSON events
- manages onboard LED state for ready, scan, enrollment, success, and error conditions

The firmware does not own student names, LRNs, attendance reports, or SQLite persistence.

### Communication

The Python communication layer owns:

- COM-port enumeration
- candidate ranking
- identity handshakes
- serial open/close operations
- buffered reads
- command writes
- disconnect detection
- automatic reconnect attempts
- device metadata and fingerprint-count synchronization

The host accepts a device only after a valid DSIS identity response with a supported protocol version.

### Application logic

Core modules keep device I/O separate from business rules:

| Module | Responsibility |
| --- | --- |
| `core/device_discovery.py` | Candidate scoring and DSIS identity handshake |
| `core/serial_handler.py` | Live serial connection and reconnect lifecycle |
| `core/attendance.py` | Parse scan events, apply app cooldown, classify confidence |
| `core/attendance_status.py` | Time-in/time-out status evaluation |
| `core/attendance_calendar.py` | Calendar exceptions and schedule lookup |
| `core/database.py` | SQLite persistence, reports, backups, exports |
| `core/permissions.py` | In-memory role and action authorization |
| `core/auth.py` | Password hashing and verification |
| `core/logger.py` | Structured console/file logging |
| `core/commands.py` | Permission-aware firmware command wrappers |

### Presentation

The active UI is under `python/gui_web/web/`.

`main_web.py` creates a native pywebview window and exposes an `Api` instance. JavaScript calls the bridge through `window.pywebview.api`.

The backend also pushes asynchronous events to the browser through:

`window.dsisEvent(event, payload)`

Examples include connection changes, scan results, enrollment progress, delete/wipe progress, logs, fingerprint-count updates, and device-mode changes.

### Persistence

The local persistence model is intentionally simple:

- SQLite for students and attendance
- JSON for saved application settings
- filesystem directories for backups, logs, exports, and generated charts

No cloud database or external web service is required for the normal DSIS workflow.

## Key architectural boundaries

### Hardware boundary

The AS608 is connected only to the ESP32 UART. The PC does not talk directly to the sensor.

### Host protocol boundary

The PC sends line-oriented commands at 115200 baud. The firmware may emit both compatibility text and JSON.

### UI boundary

The browser-facing JavaScript should not access SQLite or pyserial directly. Python remains responsible for persistence, device access, and authorization.

### Authorization boundary

The UI can hide or disable controls, but privileged operations also pass through backend permission checks. The effective role comes from an in-memory session, not the stored `current_role` display value in `settings.json`.

## Design goals

The current architecture favors:

- deterministic local operation
- modular testing
- recoverable serial connections
- clear separation of UI and business logic
- explicit device identity
- persistent configuration without cloud dependencies
- backup/restore support
- traceable logging

For the implementation contract and lifecycle details, see [v3-system.md](v3-system.md).

Last reviewed: 2026-09-20.
