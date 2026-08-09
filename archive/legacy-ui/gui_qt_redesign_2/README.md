# PySide6 UI Redesign — for Jayden-Dollaga/Fingerprint-Attendance-System

Tested against your actual repo (cloned from GitHub) — constructed the
window, switched through every page, and exercised the enroll + wipe
dialog signal flow end to end with no errors.

## IMPORTANT — where this goes
Your repo's Python code lives in the `python/` folder, not the repo root:

```
Fingerprint-Attendance-System/
  python/
    main.py
    config.py
    settings_store.py
    core/
    gui/
    services/
    gui_qt/      <-- put this folder here
```

Copy the `gui_qt` folder from this zip directly into `python/`, so it
sits next to `core/`, `gui/`, `services/`. Then, from inside `python/`:

```
pip install PySide6
python -m gui_qt.main_qt
```

(Last time this errored with `ModuleNotFoundError: No module named 'core'`
because `gui_qt/` was run standalone, outside the folder that has `core/`
in it. Running `python -m gui_qt.main_qt` from inside `python/` fixes that.)

## What's real vs. what's still a stub

**Fully wired to your backend:**
- `workers/serial_worker.py` — QThread around your real `SerialHandler` +
  `AttendanceProcessor`. Ports `read_serial_output()` /
  `_dispatch_attendance_message()` / `_handle_scan_result()` AND the
  enroll/wipe regex parsers (`RE_ENROLLING_AS`, `RE_ENROLL_SUCCESS`,
  `RE_WIPE_START`, etc. — copied verbatim from your `gui/app.py`) to Qt
  signals.
- `pages/dashboard_page.py` — real counts from `core/database.py`.
- `pages/attendance_page.py` — real Today/Recent views, live-updates on
  scan events.
- `pages/students_page.py` — full CRUD via `StudentService`, plus:
  - `EnrollDialog` — matches your real `gui/dialogs.py` flow exactly:
    the fingerprint ID is assigned by the ESP32 (not typed in), Save
    stays disabled until the "SUCCESS! Finger saved as ID #N" line
    arrives.
  - `WipeDialog` — matches your real wipe confirmation flow: sends
    `cmd_wipe`, watches for the wipe-success line, then calls
    `clear_all_data()` exactly like your `_clear_database_data()` does.
- `pages/reports_page.py` — real statistics report, CSV export, DB
  backup/restore.
- `pages/settings_page.py` — real port list, `settings_store.py`
  read/write, firmware upload via `core/firmware_helper.py`.
- `pages/logs_page.py` — now matches your `gui/log_page.py`, including
  the Clear button.
- `main_window.py` — one shared `SerialHandler` + `AttendanceProcessor`,
  real Connect/Disconnect, calls `init_database()` on startup.

**Still not ported** (wasn't asked for / lower priority):
- `gui/perf_profiler.py` — internal timing tool, no UI element needed
  unless you want a toggle for it in Settings.
- `gui/serial_troubleshooting.py`, `gui/layout_utils.py` — dialog-sizing
  and troubleshooting-message helpers specific to the Tk layout; Qt's
  layout system doesn't need the sizing helper, and the troubleshooting
  message text could be ported into a QMessageBox on connect failure if
  you want it.
- Report charts — `core/database.py` already has
  `generate_attendance_chart()` / `generate_section_chart()` /
  `generate_grade_chart()` (matplotlib PNGs). Easiest: display the PNG
  in a `QLabel` on the Reports page. Say the word and I'll wire it in.

## Known project bugs (unaddressed — live in the backend, not the UI)
Startup crash, data integrity issue on "Add Student", cooldown bypass,
orphaned `AttendanceProcessor` class. This redesign uses one single
`AttendanceProcessor` instance (owned by `MainWindow`, used by
`SerialWorker`), so if the "orphaned" class was a stray duplicate
instance somewhere in the old `app.py`, this consolidates it — but I
haven't gone hunting for the other three yet. Say the word if you want
me to dig into those next.
