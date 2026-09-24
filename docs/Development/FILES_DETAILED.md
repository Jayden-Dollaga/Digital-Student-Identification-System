# DSIS Active Python File Guide

This guide maps the maintained Python v3 implementation to the repository files that own each responsibility. Historical and reference code is identified separately.

## Entry points

| File | Role |
| --- | --- |
| `run_web_gui.py` | Root launcher for the maintained webview application |
| `python/main.py` | Compatibility entry point |
| `python/gui_web/main_web.py` | Native pywebview window lifecycle |

## Web UI

| Path | Responsibility |
| --- | --- |
| `python/gui_web/web/index.html` | Application pages and markup |
| `python/gui_web/web/app.js` | Frontend state, navigation, API calls, live events |
| `python/gui_web/web/styles.css` | Layout, themes, controls, tables, dialogs |
| `python/gui_web/api.py` | Browser-to-Python application bridge |

Current pages include Dashboard, Attendance, Students, Reports, Logs, Settings, and Calendar.

## Core backend

| Module | Responsibility |
| --- | --- |
| `python/config.py` | Runtime defaults, environment overrides, paths, role definitions |
| `python/settings_store.py` | Persistent JSON settings and setup state |
| `python/core/device_discovery.py` | COM-port enumeration, candidate scoring, DSIS identity handshake |
| `python/core/serial_handler.py` | pyserial connection, buffering, commands, disconnect/reconnect |
| `python/core/commands.py` | Permission-aware firmware command wrappers |
| `python/core/attendance.py` | JSON/text scan parsing, cooldown, confidence classification |
| `python/core/attendance_status.py` | Time-in/time-out status evaluation |
| `python/core/attendance_calendar.py` | Holiday, suspension, and half-day schedule rules |
| `python/core/database.py` | SQLite schema, students, attendance, reports, charts, backups, restore |
| `python/core/auth.py` | First-run password creation and verification |
| `python/core/permissions.py` | In-memory role sessions and action checks |
| `python/core/logger.py` | Structured console and per-run file logging |
| `python/core/utils.py` | JSON parsing and shared helpers |

## Runtime flow by module

```text
run_web_gui.py
   -> gui_web.main_web
   -> gui_web.api.Api
      -> settings_store
      -> core.auth / core.permissions
      -> core.database
      -> core.serial_handler
         -> core.device_discovery
      -> core.attendance
      -> core.attendance_status / attendance_calendar
      -> core.logger
```

The browser never opens SQLite or pyserial directly. Those operations remain behind the Python API bridge.

## Current configuration

| Setting | Default |
| --- | --- |
| Host baud | 115200 |
| Application cooldown | 10 seconds |
| Application min confidence | 100 |
| Auto-detect serial | Enabled |
| Auto-reconnect | Enabled |
| Reconnect retries | 5 |
| Reconnect base delay | 2 seconds |
| Automatic backup interval | 25 minutes |
| Theme | Dark |
| Log file output | Enabled |

## Hardware-facing source

The maintained firmware is `firmware/ESP32_DSIS_AllInOne/ESP32_DSIS_AllInOne.ino`. The fingerprint-only sketch is retained as an earlier variant.

Hardware constants in the current sketch include:

- sensor TX -> ESP32 GPIO14;
- sensor RX -> ESP32 GPIO27;
- host serial -> 115200 baud;
- AS608 UART -> 57600 baud;
- real fingerprint IDs -> 1-127.

## Authentication and permissions

Authentication is implemented by `core.auth` and sessions by `core.permissions`.

| Role | Permissions |
| --- | --- |
| Administrator | scan, enroll, delete, wipe, export, backup, restore, attendance evaluation, calendar management |
| Teacher | scan, export, backup, attendance evaluation |
| Guest | scan, attendance evaluation |

The persisted `current_role` field is not an authorization source.

## Tests relevant to v3

Important current test areas include:

- `tests/test_gui_web_smoke.py` — webview bridge/UI contract checks;
- `tests/test_v3_authentication.py` — password and session behavior;
- `tests/test_permissions_and_attendance_tagging.py` — permissions, wipe lifecycle, event tagging;
- `tests/test_attendance_status.py` — time-based attendance rules;
- `tests/test_database_*.py` — database, reset, backup, restore, and security behavior;
- `tests/physical_esp32_smoke.py` — guarded physical hardware checks.

## Historical/reference code

The following paths are not part of the supported v3 runtime:

- `archive/legacy-ui/v1/` — CustomTkinter;
- `archive/legacy-ui/v2/` — PySide6/Qt;
- `python/gui_web/v2_reference/` — v2 reference snapshot;
- `tests/Prototype/` — isolated UI previews.

Use these only when comparing historical behavior or researching regressions.

Last reviewed: 2026-09-20.