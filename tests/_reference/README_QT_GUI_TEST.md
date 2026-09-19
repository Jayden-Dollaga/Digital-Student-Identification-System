# Interactive Qt GUI Test (Historical)

> This smoke test targets the archived v2 PySide6/Qt interface. The maintained application is the v3 HTML/pywebview interface launched by `run_web_gui.py`.

This is an interactive smoke test for the archived PySide6 v2 interface. It
opens the historical application UI without requiring an Arduino or fingerprint
sensor. Use the v3 webview smoke tests and `run_web_gui.py` for the maintained
application; use this test only for parity or regression comparison.

## Install dependencies

From the repository root:

```powershell
python -m pip install -r requirements.txt
```

The archived Qt interface requires `PySide6` and `pyserial`. The full
requirements file also supports the active webview application and other tools.

## Run from the repository

From the repository root:

```powershell
python tests\qt_gui_interactive.py
```

On Windows, you can double-click `tests\run_qt_gui_test.bat`.

Check that the window opens and that Dashboard, Attendance, Students, Reports,
Logs, and Settings can all be selected. Close the window with its normal close
button; it should exit cleanly.

## Run the ZIP bundle

Extract `qt_gui_interactive_bundle.zip` to a writable folder. Open PowerShell
in the extracted folder and run:

```powershell
python qt_gui_interactive.py
```

Or double-click `run_qt_gui_test.bat` in the extracted folder.

The bundle contains the maintained `python/` runtime and Qt theme files, so it
does not depend on the original repository's current working directory.

## Optional hardware check

Close Arduino IDE's Serial Monitor first because it locks the COM port. Start
the UI, open Settings to review the port and baud rate, then click **Connect**.
A missing board should leave the UI open and report the failure in the status
area and logs. Do not use the hardware path to test ordinary navigation.

Runtime-created files are stored under `data/` by default:

- `data/attendance.db`
- `data/logs/`
- `data/backups/`
- `data/exports/`

## Automated shell check

From the repository root:

```powershell
python -m pytest tests\test_qt_shell.py -v
```
