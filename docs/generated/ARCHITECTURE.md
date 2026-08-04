# Architecture Audit

## System Layers

1. Firmware (ESP32)
   - Implements ESP32 Arduino logic for the fingerprint system.
   - Handles commands over serial: `ENROLL`, `DELETE`, `WIPE`, `LIST`, `SCAN`, `STOP`, and `ID?`.
   - Interfaces with the AS608 fingerprint sensor and onboard LED.
   - Emits both legacy plain-text outputs and JSON events.

2. Core Python Services
   - `python/config.py`: runtime config, environment overrides, serial port heuristics.
   - `python/core/serial_handler.py`: serial port management, reconnect, read buffer, command send.
   - `python/core/attendance.py`: parses ESP32 output, applies cooldown, logs attendance.
   - `python/core/database.py`: SQLite persistence for student profiles, attendance logs, exports, and backups.
   - `python/core/device_discovery.py`: serial port discovery with JSON handshake validation.
   - `python/core/logger.py`: centralized structured logging to console and optionally file.
   - `python/core/firmware_helper.py`: firmware candidate discovery and esptool-based upload.
   - `python/core/utils.py`: shared helpers for JSON parsing, display formatting, and exports.

3. Desktop UI
   - Legacy CustomTkinter stack in `python/gui/`.
   - Modern Qt/PySide6 stack in `python/gui_qt/`.
   - Shared workflow: connect to ESP32, enroll fingerprints, scan attendance, manage students, backup/restore, export reports.

4. Data Storage
   - SQLite database located in `data/attendance.db` by default.
   - Local storage for backups, exports, and application settings.

5. Tests
   - Regression test coverage in `tests/` for serial discovery, GUI pages, data handling, firmware helpers, and configuration.

## Component Responsibilities

- `python/main.py`
  - Legacy console application entry point.
  - Handles commands and prints live ESP32 responses.

- `run_qt_gui.py`
  - Launcher for the Qt-based interface.

- `python/gui_qt/main_qt.py`
  - Creates `QApplication`, loads stylesheet, and launches `MainWindow`.

- `python/gui_qt/main_window.py`
  - Orchestrates Qt pages and background serial worker.
  - Manages connect/disconnect and scan toggle.

- `python/gui_qt/workers/serial_worker.py`
  - Reads serial lines on a worker thread.
  - Emits Qt signals for scan events, connection state, enroll/wipe progress, logs, and errors.

- `python/gui_qt/pages/*`
  - Individual pages for attendance, dashboard, students, reports, logs, and settings.

- `python/services/*`
  - Thin wrappers around database operations and export/backup behaviors.

- `python/settings_store.py`
  - JSON-based persistence for UI settings, themes, serial preferences, and auto-detect toggles.

## Deployment Notes

- The repository contains both source code and deployment artifacts for Windows.
- `run_app.bat` starts the legacy GUI.
- `run_qt_gui.py` and `run_qt_gui.bat` start the Qt GUI.
- `install_requirements.bat` installs Python dependencies from `requirements.txt`.

## Audit Findings

- The project has a clear separation between serial I/O, attendance logic, persistence, and UI.
- Two GUI stacks are present; the Qt stack is a newer alternative while the legacy CustomTkinter code remains functional.
- Existing documentation under `docs/` is substantial but scattered, so `docs/generated/` provides a consolidated repository audit.
- Serial discovery and JSON handshake support are implemented to reduce manual port selection.

## Recommendations

- Continue migrating user-facing functionality into the Qt stack to reduce maintenance overhead.
- Add a dedicated `docs/generated/FILE_INVENTORY.md` if a full file-level audit is required.
- Ensure `README.md` references the `docs/generated/` audit artifacts for maintainers.
