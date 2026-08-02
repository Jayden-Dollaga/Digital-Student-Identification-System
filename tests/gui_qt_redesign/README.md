# PySide6 UI Redesign — Starter Scaffold

## How to run
```
pip install PySide6
python -m gui_qt.main_qt
```
Run this from the folder that CONTAINS `gui_qt/` (i.e. your project root,
alongside your existing `main.py`, `database.py`, `serial_handler.py`, etc.)

## What's here
- `main_qt.py` — new entry point, loads the QSS theme and launches the window.
  Your existing `main.py` is untouched — run either one while you migrate.
- `theme.qss` — dark theme, one accent color (#4C8DFF). Edit this file to
  reskin the whole app without touching Python.
- `main_window.py` — the shell: sidebar + header (page title, live
  connection status) + stacked pages. This is your new `app.py`.
- `widgets/sidebar.py`, `widgets/stat_card.py` — reusable pieces.
- `pages/*.py` — one file per page, matching your existing gui/ layout
  (dashboard, attendance, students, reports, logs, settings).
- `workers/serial_worker.py` — QThread wrapping ESP32 I/O so scans never
  block the UI. Emits `connection_changed`, `scan_event`, `log_line`, `error`
  signals that MainWindow already wires up to the right pages.

## What you need to do next
Every `# TODO` comment marks a spot where a stub needs to be replaced with
a call into your real backend:

1. **`workers/serial_worker.py`** — swap `_connect_stub` /
   `_read_line_stub` / `_parse_stub` for real calls into
   `serial_handler.py`, `commands.py`, and `attendance.py`.
2. **`pages/dashboard_page.py`, `attendance_page.py`, `students_page.py`**
   — swap the empty `rows = []` placeholders for real `database.py` queries.
3. **`pages/settings_page.py`** — wire `port_combo` / `baud_combo` /
   `auto_reconnect` to `settings_store.py`, and `on_upload_firmware` to
   `firmware_helper.py`.
4. **`pages/reports_page.py`** — `on_export_clicked` → `database.py` export
   function. If you want a trend chart, `PySide6.QtCharts` keeps it all in
   Qt with no extra dependency.

## Why this structure
- Backend modules (`database.py`, `serial_handler.py`, `commands.py`,
  `attendance.py`, `config.py`, `settings_store.py`, `firmware_helper.py`)
  are untouched. Only the UI layer changes.
- `SerialWorker` runs on its own `QThread` and talks to the UI only through
  signals — this is the thread-safe way to push live scan events into
  widgets, and it's the main reason PySide6 fits this project better than
  CustomTkinter for a hardware-driven app.
- Packaging: point your existing `build_portable.bat` /
  `fingerprint_portable.spec` at `main_qt.py` instead of `main.py` once
  you're happy with the redesign, and add PySide6 to the PyInstaller
  hidden-imports / collect-all list (Qt needs its plugin DLLs bundled).

## Known project bugs (not addressed by this redesign)
These live in the backend/data layer, not the UI, so they'll carry over
until fixed separately: startup crash, data integrity issue on "Add
Student", cooldown bypass flaw, and an orphaned `AttendanceProcessor`
class.
