FILES_DETAILED.md
=================

This file was generated programmatically. It summarizes each Python source file in the
repository by extracting the top-level module docstring or leading comment block and
adding a one-line purpose summary. It is intended as a developer reference.

---

1) python/config.py
--------------------
Doc excerpt:
"""Configuration helpers for the fingerprint attendance system.

The module now exposes a small config dataclass and environment-aware helpers
without doing expensive serial discovery during import time.
"""

Purpose: Provide `AppConfig`, environment-aware resolution of runtime paths, and helper
functions for serial port discovery and default settings.

2) python/settings_store.py
---------------------------
Doc excerpt: (no module docstring) leading contents show it manages a JSON settings file
and provides `load_settings()` / `save_settings()` helpers.

Purpose: Persist and load small UI settings JSON file under the project's data directory.

3) python/core/__init__.py
-------------------------
Doc excerpt: """Core package for attendance system logic.

Exports:
- Database functions for student and attendance management
- Serial handler for ESP32 communication
- Command functions for fingerprint operations
- Logger for application events
"""

Purpose: Package initializer and short listing of exported core responsibilities.

4) python/core/logger.py
------------------------
Doc excerpt: Header comment explaining centralized logging, rotating file output, and
structured message formatting. Implements `LOG` configuration and helper functions
(`debug`, `info`, `success`, etc.) and provides `log = LoggerProxy()`.

Purpose: Centralized application logging (console + timed rotating file handlers).

5) python/core/database.py
--------------------------
Doc excerpt: """Persistence layer for students, attendance events, reports, and backup helpers.

This module centralizes SQLite access for the fingerprint attendance system and
keeps the rest of the application focused on workflow logic instead of raw SQL.
"""

Purpose: Main DB layer — schema initialization, CRUD helpers for students and attendance,
report generation, and chart/export helpers. Provides `get_connection()` returning a
`ManagedConnection` context wrapper.

6) python/core/serial_handler.py
--------------------------------
Doc excerpt: Module docstring: "Serial communication boundary for the ESP32 fingerprint device."

Purpose: Encapsulates `pyserial` usage, reconnect logic, read/write helpers used by GUI workers.

7) python/gui_qt/main_qt.py
-------------------------
Doc excerpt: Module docstring: Launcher for the PySide6-based Qt interface.

Purpose: Qt entrypoint — loads stylesheet, constructs `MainWindow`, and runs the Qt event loop.

8) python/gui_qt/main_window.py
------------------------------
Doc excerpt: (no module docstring) file defines `MainWindow` using PySide6 and composes pages,
serial worker, and application lifecycle glue.

Purpose: Main UI host for the PySide6 GUI; wires pages, serial worker, and page switching.

9) tools/_database_refactor.py
------------------------------
Doc excerpt: (no top docstring) contains a near-copy of DB helper code used during refactors.

Purpose: Developer tool used for refactor work; now delegates `get_connection()` to `core.database`.

10) tools/debug_db_connections.py
---------------------------------
Doc excerpt: (no top docstring) debug helper that tracks sqlite3 connections and prints counts.

Purpose: Detect unclosed sqlite3 connections during debugging; now safely closes tracked connections.

11) tools/verify_gui_startup.py
------------------------------
Doc excerpt: small helper that imports the legacy `customtkinter` app and runs its `main()`
with the mainloop stubbed out to test startup.

Purpose: Script to detect whether the legacy CTk GUI can be imported and initialized safely.

12) python/testing_area/services/excel_export.py
----------------------------------------------
Doc excerpt: file header explaining Excel export helpers for attendance records using `openpyxl`.

Purpose: Example/export helper that writes attendance to XLSX files. Lives in `testing_area`.

13) python/testing_area/services/backup.py
----------------------------------------
Doc excerpt: header describing simple copy-based DB backup to data/backups/.

Purpose: Small reference script demonstrating how to copy DB to backups folder.

14) tests/legacy/* (phase2_databasev*.py)
----------------------------------------
Doc excerpt: Large header comments in each legacy script explaining how to run a serial-to-sqlite
phase2 demo; these scripts historically used `sqlite3.connect(DB_FILE)`. They were updated to use
the project's `core.database.get_connection()` and set `FINGERPRINT_DB_PATH` so they reuse the
same PRAGMA/settings and ManagedConnection wrapper.

Purpose: Legacy example scripts used for manual instrumented testing with an ESP32 connected.

---

If you want the full file-by-file dump of every Python file's top docstring and the first
non-empty comment line, I can append it below or save it as a more verbose `FILES_EXTRACT.md`.

Next: I will run the entire test suite and fix any failing tests or lingering ResourceWarning traces.
