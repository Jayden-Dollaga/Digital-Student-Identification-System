# DSIS Project File Overview

This is the current source-tree map for DSIS. The maintained desktop runtime is the v3 HTML/pywebview application. Historical Qt and CustomTkinter implementations are retained for reference under `archive/legacy-ui/`.

## Top-level structure

| Path | Purpose |
| --- | --- |
| `python/` | Active Python backend, web UI, services, and compatibility modules |
| `firmware/` | ESP32/AS608 sketches and hardware tests |
| `tests/` | Automated tests and isolated UI prototypes |
| `docs/` | User, architecture, hardware, API, development, history, and generated documentation |
| `Build/` | PyInstaller specifications and build outputs |
| `data/` | Runtime database, settings, backups, logs, charts, and exports |
| `tools/` | Diagnostics, packaging helpers, and maintenance tools |
| `archive/` | Historical implementations and diagnostics |

## Active launch path

```text
run_web_gui.py / run_web_gui.bat
        -> python/gui_web/main_web.py
        -> python/gui_web/api.py
        -> python/core/*
        -> data/ + ESP32/AS608
```

The active frontend is `python/gui_web/web/`. It communicates with Python through `window.pywebview.api` and receives asynchronous backend events through `window.dsisEvent`.

## Core modules

| Module | Responsibility |
| --- | --- |
| `python/config.py` | Runtime defaults, paths, environment overrides, role definitions |
| `python/settings_store.py` | Persistent settings and setup state |
| `python/core/device_discovery.py` | Serial-port scoring and DSIS identity handshake |
| `python/core/serial_handler.py` | Serial lifecycle, buffering, reconnect |
| `python/core/attendance.py` | Scan parsing, cooldown, confidence classification |
| `python/core/attendance_status.py` | Time-based status calculation |
| `python/core/attendance_calendar.py` | Holiday/suspension/half-day schedule rules |
| `python/core/database.py` | SQLite schema, records, reports, backups, restore |
| `python/core/auth.py` | First-run password hashing/verification |
| `python/core/permissions.py` | In-memory session role and authorization |
| `python/core/logger.py` | Console and per-run file logging |
| `python/gui_web/api.py` | Frontend/backend application bridge |

## Active firmware

`firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino` is the maintained device firmware.

| Property | Value |
| --- | --- |
| Device | Digital Student Identification System |
| Firmware | 1.0.10 |
| Protocol | 1 |
| Host serial | 115200 |
| AS608 UART | 57600 |
| Sensor TX | ESP32 GPIO14 |
| Sensor RX | ESP32 GPIO27 |

## Runtime data

Default runtime paths are `data/attendance.db`, `data/settings.json`, `data/backups/`, `data/logs/`, `data/charts/`, and `data/exports/`.

Do not commit production runtime data.

## Testing

Relevant current test areas include:

- `tests/test_gui_web_smoke.py` — v3 web bridge and UI smoke behavior;
- `tests/test_v3_authentication.py` — authentication/session behavior;
- `tests/test_permissions_and_attendance_tagging.py` — permissions, wipe, and event tagging;
- `tests/test_attendance_status.py` — attendance status rules;
- `tests/test_database_*.py` — database behavior;
- `tests/physical_esp32_smoke.py` — guarded hardware validation.

## Historical/reference paths

- `archive/legacy-ui/v1/` — CustomTkinter v1;
- `archive/legacy-ui/v2/` — PySide6/Qt v2;
- `python/gui_web/v2_reference/` — v2 reference snapshot;
- `tests/Prototype/` — isolated UI previews.

These paths are not the supported v3 launch path.

## Related documentation

- [v3 Architecture](../Architecture/v3-system.md)
- [Software Flow](../Architecture/software-flow.md)
- [Database Schema](../Architecture/database-schema.md)
- [API Reference](../API/README.md)
- [v3 Workflows](../UserGuide/v3-workflows.md)

Last reviewed: 2026-09-20.