# GUI Audit

> Historical generated snapshot. The **active interface is v3 HTML/pywebview**. The v1 CustomTkinter and v2 Qt stacks are archived/reference implementations and are not supported launch paths.

## Active interface

The maintained Windows desktop UI is:

- `run_web_gui.py` — source launcher from the repository root.
- `run_web_gui.bat` — Windows convenience launcher.
- `python/gui_web/main_web.py` — pywebview window lifecycle.
- `python/gui_web/api.py` — JavaScript-to-Python bridge exposed through `window.pywebview.api`.
- `python/gui_web/web/` — HTML/CSS/JavaScript application assets.

The v3 application uses the shared Python services for serial communication, attendance processing, SQLite persistence, permissions, authentication, backups, exports, and diagnostics.

## Archived / reference interfaces

### v1 CustomTkinter

Historical source is retained under `archive/legacy-ui/v1/`. It is useful for historical comparison and maintenance archaeology but is not the current DSIS launcher.

### v2 PySide6 / Qt

Historical source is retained under `archive/legacy-ui/v2/`. It contains the previous Qt implementation and related tests/reference material. It is not the current production UI.

`python/gui_web/v2_reference/` also contains reference material used while migrating behavior into v3; it should not be treated as a second supported desktop application.

## Current UI capabilities

The maintained v3 UI exposes the supported DSIS workflows through the webview bridge:

- Connect / disconnect the ESP32.
- Start / stop fingerprint attendance scanning.
- Enroll fingerprints and associate them with student records.
- Delete individual fingerprints or wipe device fingerprints.
- Manage student records.
- View attendance history and evaluation windows.
- Export CSV reports.
- Back up and restore the local SQLite database.
- Configure serial, attendance, schedule, branding, and application settings according to the active permission model.
- View live application/device diagnostics and logs.

## Serial boundary

The v3 desktop application uses **115200 baud** for PC ↔ ESP32 communication. The ESP32 uses **57600 baud** internally for the AS608 UART. These are separate links; the desktop application does not open the AS608 connection directly.

## Historical documentation note

Older generated files may still mention the v1/v2 paths because they are snapshots of previous repository states. They should be read as historical audit material unless explicitly marked as current.
