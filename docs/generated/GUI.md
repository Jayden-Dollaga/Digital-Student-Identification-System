# GUI Audit

## Overview

The project includes two desktop user interfaces:

- Legacy CustomTkinter UI in `python/gui/`
- Modern PySide6 Qt UI in `python/gui_qt/`

Both interfaces share the same backend services and serial workflow, but the Qt stack represents a cleaner separation of UI from core services.

## Legacy CustomTkinter stack

Key modules:

- `python/gui/app.py` — main application shell and orchestration.
- `python/gui/sidebar.py` — left-hand sidebar with connection and actions.
- `python/gui/attendance_page.py` — attendance list view.
- `python/gui/students_page.py` — student roster management.
- `python/gui/dashboard.py` — summary dashboard.
- `python/gui/reports_page.py` — reporting and export screens.
- `python/gui/settings_page.py` — settings and serial preferences.
- `python/gui/dialogs.py` — modal dialogs for enroll, wipe, restore, and firmware operations.
- `python/gui/serial_troubleshooting.py` — user-facing troubleshooting help for serial connections.

The legacy UI is driven by CustomTkinter components and manually updated state.

## Qt/PySide6 stack

Key modules:

- `python/gui_qt/main_qt.py` — PySide6 application entry point.
- `python/gui_qt/main_window.py` — main window, sidebar, header, page routing, and serial worker integration.
- `python/gui_qt/workers/serial_worker.py` — background thread reading serial data and emitting Qt signals.
- `python/gui_qt/pages/` — individual page widgets for attendance, dashboard, students, reports, logs, and settings.
- `python/gui_qt/widgets/` — reusable UI widgets such as the sidebar and stat cards.

The Qt stack is designed to keep device I/O off the UI thread and to surface events through signals.

## Shared UI capabilities

- Connect / disconnect ESP32.
- Start / stop attendance scanning.
- Enroll fingerprints and link them to student records.
- Delete or wipe fingerprint data.
- View attendance records and dashboards.
- Export data and backup/restore the local database.
- Adjust settings such as COM port, baud rate, theme, and auto-connect behavior.

## Observations

- The Qt stack currently provides a more modern and responsive interface.
- The legacy stack remains present and useful for compatibility with earlier installations.
- Serial worker logic in `python/gui_qt/workers/serial_worker.py` mirrors the legacy app's parsing behavior, helping maintain consistency across both UI options.
