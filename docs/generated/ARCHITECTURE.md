# Architecture Audit

> Historical generated snapshot. The current architecture is documented in `docs/Architecture/system-architecture.md`; the **active UI is v3 HTML/pywebview** under `python/gui_web/` and is launched by `run_web_gui.py` / `run_web_gui.bat`.

## System layers

1. **Firmware (ESP32 + AS608)**
   - Maintained sketch: `firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino`.
   - Host serial protocol uses **115200 baud**.
   - Internal ESP32 ↔ AS608 UART uses **57600 baud**.
   - Supports identity, scan, enrollment, deletion, wipe, list, stop, and status operations.
   - Emits compatibility text and structured JSON events.

2. **Core Python services**
   - `python/config.py`: runtime configuration and environment overrides.
   - `python/core/serial_handler.py`: COM-port discovery, connection, reconnect, buffering, and command I/O.
   - `python/core/device_discovery.py`: device probing and DSIS identity handshake.
   - `python/core/attendance.py`: serial-event parsing, confidence handling, cooldown, and attendance recording.
   - `python/core/database.py`: SQLite schema, student records, attendance, reports, backups, and exports.
   - `python/core/auth.py`: password hashing and verification.
   - `python/core/permissions.py`: session roles and operation permissions.
   - `python/core/logger.py`: structured application logging.
   - `python/core/firmware_helper.py`: firmware discovery/upload helpers.
   - `python/core/utils.py`: shared parsing/export helpers.

3. **Desktop UI**
   - `python/gui_web/`: maintained v3 HTML/pywebview application.
   - `run_web_gui.py`: supported source launcher.
   - `run_web_gui.bat`: supported Windows convenience launcher.
   - `archive/legacy-ui/v1/`: archived CustomTkinter UI.
   - `archive/legacy-ui/v2/`: archived PySide6/Qt UI.
   - `python/gui_web/v2_reference/`: migration/reference material, not a supported second UI.

4. **Local data storage**
   - SQLite database: `data/attendance.db` by default.
   - Settings/authentication: `data/settings.json`.
   - Backups: `data/backups/`.
   - Logs, charts, and exports are also kept under `data/`.
   - Runtime data is intentionally excluded from version control.

5. **Testing and CI**
   - Automated tests live under `tests/`.
   - Hardware tests are marked separately because a physical ESP32/AS608 is required.
   - `.github/workflows/tests.yml` compiles the active Python tree, runs automated tests, runs archived UI marker suites, and checks the active JavaScript syntax.

## Active request flow

```text
Windows user
    │
    ▼
run_web_gui.py / run_web_gui.bat
    │
    ▼
pywebview + python/gui_web/web/
    │ window.pywebview.api
    ▼
python/gui_web/api.py
    │
    ├── core/permissions + core/auth
    ├── core/attendance
    ├── core/database ──> data/attendance.db
    └── core/serial_handler
              │ 115200
              ▼
            ESP32
              │ 57600
              ▼
            AS608
```

## Deployment notes

The supported source launch is `python run_web_gui.py`. The supported v3 PyInstaller specification is `Build/DSIS_v3.spec`. The older `run_app.bat`, `run_qt_gui.py`, and related v1/v2 launchers belong to historical/reference code and should not be presented as current release launchers.

## Audit note

This file is a generated/historical architecture snapshot, not the source of truth for every implementation detail. For current behavior, prefer the active code and the current documents linked from `README.md`, `INSTALLATION.md`, `PORTABLE_BUILD.md`, and `docs/Architecture/`.
