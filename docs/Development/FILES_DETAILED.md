# Active Python File Guide

This guide replaces the older generated inventory that described the v1/v2 UI trees as current. It summarizes the maintained v3 source tree at commit `aa457e0`.

## Entry points

- `run_web_gui.py`: adds the Python and web GUI paths, then launches `gui_web.main_web.main()`.
- `python/main.py`: compatibility entry point that delegates to the v3 webview launcher.
- `python/gui_web/main_web.py`: creates the native pywebview window, loads `web/index.html`, connects the API object, and disconnects cleanly when the window closes.

## Web UI and bridge

- `python/gui_web/api.py`: the JSON-safe bridge exposed as `window.pywebview.api`. It coordinates connection, serial events, enrollment, deletion, wipe, settings, database queries, reports, backups, attendance evaluation, and CSV export.
- `python/gui_web/web/index.html`: page shell, navigation, dashboard, attendance, students, reports, logs, and settings markup.
- `python/gui_web/web/app.js`: frontend state, navigation, pywebview readiness, event handling, serial controls, enrollment flow, evaluation rendering, and export actions.
- `python/gui_web/web/styles.css`: current light/dark theme variables, layout, controls, tables, dialogs, and evaluation components.
- `python/gui_web/v2_reference/`: reference-only PySide6 source snapshot used to compare workflow and serial contracts; it is not imported by v3.

## Backend

- `python/config.py`: `AppConfig`, environment overrides, serial defaults, role definitions, logging, backup, and data paths.
- `python/settings_store.py`: JSON persistence for port, baud, theme, cooldown, confidence, role, auto-detection, reconnect, logging, and backup preferences.
- `python/core/serial_handler.py`: pyserial boundary, port opening, command writes, buffered reads, handshake metadata, disconnects, and reconnects.
- `python/core/device_discovery.py`: port scoring, VID/PID hints, boot capture, identity handshake, and candidate probing.
- `python/core/commands.py`: validated newline-terminated firmware commands.
- `python/core/attendance.py`: JSON/text parsing, cooldown, confidence handling, and attendance outcomes.
- `python/core/database.py`: SQLite schema, reserved `fingerprint_id = 0` row, students, attendance, statistics, evaluation inputs, backups, restore validation, and exports.
- `python/core/permissions.py`: role-based local action checks.
- `python/core/logger.py`: structured console and per-run file logging.
- `python/core/utils.py`: JSON parsing, formatting, and shared utility functions.
- `python/core/firmware_helper.py`: historical firmware candidate and upload helpers; the supported upload path is Arduino IDE with the all-in-one sketch.

## Services and archived/reference code

- `python/services/`: thin compatibility wrappers around database and export operations; the active v3 API calls core functions directly for most workflows.
- `python/gui/` and `python/gui_qt/`: compatibility/reference packages retained for tests and migration comparison.
- `archive/legacy-ui/v1/`: historical CustomTkinter application.
- `archive/legacy-ui/v2/`: historical PySide6/Qt application.

## Validation

- `tests/test_gui_web_smoke.py`: active v3 bridge and UI smoke coverage.
- `tests/test_database_*.py`: schema, reset, backup, restore, and security coverage.
- `tests/test_permissions_and_attendance_tagging.py`: role and attendance behavior.
- `tests/Prototype/`: isolated visual previews, not production workflows.

For the current launch and architecture workflow, see [FILES_OVERVIEW.md](FILES_OVERVIEW.md), [system-architecture.md](../Architecture/system-architecture.md), and [testing-results.md](../UserGuide/testing-results.md).

Last reviewed: 2026-09-11, against commit `aa457e0`.
