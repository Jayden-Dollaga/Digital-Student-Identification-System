# Project File Overview

This is a current map of the active DSIS source tree. Historical Qt and CustomTkinter files remain under `archive/legacy-ui/` and are not active launchers.

## Top-level files

- `README.md` and `INSTALLATION.md`: user onboarding and hardware setup.
- `requirements.txt`: Python dependencies for the webview application, reporting, testing, and archived interfaces.
- `run_web_gui.py` and `run_web_gui.bat`: active HTML/pywebview launchers.
- `DSIS.spec` and `build_exe.bat`: current PyInstaller packaging workflow.
- `firmware/`: Arduino sketches and firmware references.
- `python/`: application backend and active web UI.
- `tests/`: automated tests and prototype previews.
- `docs/`: maintained guides, architecture notes, and historical/generated reports.
- `archive/`: legacy UI snapshots, diagnostics, and experimental material.

## Active Python modules

- `python/main.py`: compatibility entry point for the active webview application.
- `python/config.py`: environment-aware configuration and runtime paths.
- `python/settings_store.py`: persistent local UI settings.
- `python/core/database.py`: SQLite students, attendance, reports, charts, backups, and restore operations.
- `python/core/serial_handler.py`: serial connection, discovery, reading, commands, and reconnect behavior.
- `python/core/attendance.py`: scan parsing, normalization, cooldown, and attendance decisions.
- `python/core/logger.py`: centralized console and per-run file logging.
- `python/core/commands.py`: firmware command wrappers and validation.
- `python/services/`: higher-level attendance and student operations.
- `python/gui_web/main_web.py`: native webview window lifecycle.
- `python/gui_web/api.py`: JavaScript-to-Python bridge for database, serial, settings, reports, and logs.
- `Api.get_attendance_evaluation()`: day/week/month attendance evaluation and rate categorization.
- `Api.export_attendance_evaluation_csv()`: permission-gated CSV export for the selected evaluation.
- `python/gui_web/web/`: active HTML, CSS, and JavaScript interface.

## Compatibility and reference code

- `python/gui/` and `python/gui_qt/`: compatibility packages retained for tests or reference; the supported launch workflow is webview v3.
- `python/gui_web/v2_reference/`: source snapshot of the proven Qt implementation used for parity comparison; it is not imported by v3 at runtime.
- `archive/legacy-ui/`: versioned historical Qt and CustomTkinter UI trees.
- `tests/Prototype/`: isolated visual prototypes using mock or display-only data.

## Running locally

Install dependencies from the repository root:

```powershell
python -m pip install -r requirements.txt
```

Launch the active application:

```powershell
python run_web_gui.py
```

Run the automated tests:

```powershell
python -m pytest -q --disable-warnings
```

Hardware-dependent serial and fingerprint workflows require a connected ESP32 and AS608 sensor. The active build and launcher details are documented in [PORTABLE_BUILD.md](../../PORTABLE_BUILD.md).

Last reviewed: 2026-09-10, against commit `69e563b`.
