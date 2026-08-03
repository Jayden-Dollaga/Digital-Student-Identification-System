Project file overview

This file summarizes the purpose of the main files and folders in the repository. Use it as a quick reference when exploring or making changes.

Top-level files

- README.md: Project readme and quickstart.
- INSTALLATION.md: Installation notes and platform tips.
- requirements.txt: Python dependencies (updated to include PySide6 and matplotlib).
- run_qt_gui.py / run_app.bat: Convenience launchers for the app.
- LICENSE: Project license.
- pytest.ini: Pytest configuration for running tests.
- tools/: Utility scripts used for development, debugging, and building a portable executable.

Folders

- docs/: Documentation, screenshots, architecture notes, and guides including:
  - Project Overview.md: high-level summary of the project and goals.
  - System Architecture.md / architecture.md: architecture notes and diagrams.
  - LOGGING_SUMMARY.md, LOGGER_USAGE.md: logging design and usage.
  - DATABASE_*: DB change notes, schema and migration examples.
  - Installation Guide.md / PORTABLE_BUILD.md: packaging and deploy notes.

- firmware/: Arduino/ESP32 firmware sources and prebuilt binaries used with the fingerprint reader.
  - enrollment and test sketches live under subfolders like `enroll/`, `attendance/`, `prebuilt/`.

- python/: Python application source. Key areas:
  - config.py: Environment-aware configuration and `get_config()` used across the app.
  - main.py: CLI/entry helpers for non-GUI workflows.
  - services/: Business logic wrappers that use `core` for persistence and device interactions.
  - core/: Core platform helpers and integration code:
    - `database.py`: SQLite access layer (creates DB, queries, reports, charts). Returns dictionaries/TypedDicts.
    - `serial_handler.py`: Serial port connection, read/write and simple reconnection logic (depends on `pyserial`).
    - `commands.py`, `utils.py`, `firmware_helper.py`, `logger.py`: low-level helpers and centralized logging (rotation-based).
  - gui/: Legacy CustomTkinter GUI (uses `customtkinter` and `Pillow` for images).
    - `app.py`: Legacy app bootstrap.
    - `dashboard.py`, `attendance_page.py`, etc.: Legacy UI pages and dialogs.
  - gui_qt/: Newer PySide6 Qt-based GUI.
    - `main_qt.py`: Qt application entry.
    - `main_window.py`: MainWindow wiring for pages and worker lifecycle.
    - `pages/`, `widgets/`, `workers/`: Qt pages (Dashboard, Reports, Students, Attendance, Logs) and background workers (SerialWorker).

- tests/: Unit and integration tests for the Python code. Many tests cover GUI components, database features, serial handling, and app-level integration. See tests starting with `test_*.py` and `legacy/` helper test scripts.

- data/: Runtime data directory created at first run. It contains the SQLite DB (`attendance.db`) and generated charts/backups.

- tools/: developer utilities
  - `debug_db_connections.py`: utility to detect unclosed sqlite connections (now safe: tracks and closes connections manually).
  - `_database_refactor.py`: helper script used during refactors.
  - `portable_bootstrap.bat`, `build_portable.bat`, `fingerprint_portable.spec`: packaging helpers for building a portable executable with PyInstaller.

Notes & how the code is organized

- Persistence: `python/core/database.py` centralizes all DB access. Use `get_connection()` to acquire a context-managed connection; functions either use `with get_connection() as conn:` or explicitly close returned `ManagedConnection` instances. The DB layer exposes small helper functions for student and attendance operations, report generation, and chart creation (uses `matplotlib` when available).

- Serial I/O: `python/core/serial_handler.py` implements the serial abstraction using `pyserial` and is consumed by GUI workers (Qt and legacy) to process incoming fingerprint events.

- GUI: Two UI implementations exist:
  - `python/gui` (legacy) — uses `customtkinter`.
  - `python/gui_qt` (preferred for new work) — uses `PySide6`, QThread-based workers, and pages/widgets for a modular UI.

- Services: `python/services` contains higher-level operations that coordinate `core` and GUI logic (saving attendance events, importing/exporting students, backups).

- Tests: Run unit tests with `python -m unittest discover` or run specific test modules. Some tests import PySide6 or `customtkinter` and will require those packages to be installed in your environment.

Running locally

1. Create virtualenv and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the Qt GUI:

```powershell
python run_qt_gui.py
```

3. Run tests (recommended to install test dependencies first):

```powershell
pip install -r requirements.txt
python -m unittest discover -v
```

If you prefer the legacy CustomTkinter UI, run `python python/gui/app.py` or use `run_app.bat` on Windows.

If you'd like, I can expand this file to include a fully enumerated, per-file docstring-extracted summary for every Python file in the repository — that will take a bit longer but I can generate it programmatically and add it under `docs/` as `FILES_DETAILED.md`.

Detailed Python files (concise purpose)

- `python/__init__.py`: package marker for the app.
- `python/main.py`: alternate/non-GUI entry points and CLI helpers.
- `python/config.py`: application configuration (AppConfig, env-aware paths, DB path resolution).
- `python/settings_store.py`: small persistence for UI settings (local store helper).

Core package
- `python/core/__init__.py`: core package initializer.
- `python/core/database.py`: SQLite persistence layer (students, attendance, reports, charts, backups).
- `python/core/serial_handler.py`: Serial port abstraction using `pyserial` (connect/read/write/reconnect).
- `python/core/logger.py`: Centralized logging configuration and helper logger wrapper (rotating/timed file handlers).
- `python/core/firmware_helper.py`: Helpers to manage firmware upload or build artifacts for ESP32 devices.
- `python/core/commands.py`: Command constants and small CLI helpers used by the app.
- `python/core/utils.py`: Generic helper utilities used across services and CLI.
- `python/core/attendance.py`: lightweight attendance processing helpers (parsing, normalization).

Services
- `python/services/__init__.py`: service package init.
- `python/services/student_service.py`: higher-level flows for creating/updating/importing students.
- `python/services/attendance_service.py`: coordination logic for recording attendance events and exporting reports.

GUI (legacy - CustomTkinter)
- `python/gui/__init__.py`: legacy GUI package init.
- `python/gui/app.py`: bootstrap for the legacy CustomTkinter application.
- `python/gui/dashboard.py`: legacy dashboard page (widgets using customtkinter).
- `python/gui/attendance_page.py`: legacy attendance UI page.
- `python/gui/reports_page.py`: legacy reports UI (includes image handling via Pillow for export previews).
- `python/gui/log_page.py`: legacy log viewer UI.
- `python/gui/settings_page.py`: legacy settings view.
- `python/gui/students_page.py`: legacy students management UI.
- `python/gui/sidebar.py`, `python/gui/theme.py`, `python/gui/dialogs.py`, `python/gui/layout_utils.py`: UI support utilities, theming and dialogs for the legacy UI.
- `python/gui/serial_troubleshooting.py`: helper UI page for serial debugging and port probing.

GUI (Qt - PySide6)
- `python/gui_qt/__init__.py`: Qt GUI package init.
- `python/gui_qt/main_qt.py`: Qt application entry point (creates QApplication and MainWindow).
- `python/gui_qt/main_window.py`: MainWindow wiring, page switching, lifecycle shutdown handling (coordinates worker stop/wait).
- `python/gui_qt/theme.qss`: Qt stylesheet used by the Qt UI.
- `python/gui_qt/widgets/stat_card.py`, `python/gui_qt/widgets/sidebar.py`: reusable UI widgets used by the Qt pages.
- `python/gui_qt/pages/dashboard_page.py`, `attendance_page.py`, `reports_page.py`, `students_page.py`, `logs_page.py`, `settings_page.py`: Qt page implementations providing modern UI for the app.
- `python/gui_qt/workers/serial_worker.py`: QThread-based background worker to read serial events and emit signals to UI.

Testing and helper code
- `python/testing_area/*`: playground and ad-hoc scripts used during development and refactors (examples and snippets).
- `tests/`: test suite covering DB, GUI, serial handling, and integration scenarios. See tests prefixed with `test_`.

Non-workflow helpers
- `python/non_workflow/*`: legacy one-off utilities and experiments (not used by main flows).

If you'd like, I will now programmatically extract the first docstring and the top-level comments from each Python file and generate `docs/FILES_DETAILED.md` with those excerpts plus a one-line summary. That will produce a full file-by-file map you can include in the repo.
