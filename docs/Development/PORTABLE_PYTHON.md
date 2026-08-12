# Portable Python for DSIS

This document describes the optional, self-contained portable Python runtime used for DSIS development, testing, and portable deployments.

Overview
--------
- Location: `system/python/` (the portable interpreter executable should be placed here).
- Purpose: provide an isolated interpreter with required runtime packages so DSIS can be launched without touching the system Python installation.

How it works
------------
- Place an official embeddable/portable Python distribution inside `system/python/` so the interpreter is available at `system/python/python.exe` (Windows) or `system/python/python` (POSIX).
- Use `tools/runtime_manager.py` to detect the interpreter, verify required packages, launch `run_qt_gui.py` using the portable interpreter, or run tests via `python -m pytest` using the portable interpreter.

Notes and limitations
---------------------
- This repository does not include the Python runtime itself for size and licensing reasons. The embeddable Python can be downloaded from https://www.python.org/ftp/python/ and placed into `system/python/`.
- The manager will not modify your global Python installation or PATH.
- Hardware (ESP32) is not required for basic software validation, but serial behaviour may be partially untested without a device.

Typical workflow
----------------
1. Download the official embeddable/embeddable-amd64 zip for your Python version from python.org.
2. Extract the contents into `system/python/` so `system/python/python.exe` exists.
3. Install packages into the portable interpreter if required. Example:

```powershell
# Example: from a system shell
system\python.exe -m pip install PySide6 pyserial Pillow matplotlib openpyxl
```

4. Run the runtime manager:

```powershell
python tools/runtime_manager.py
```

5. Click `Check Environment` and `Verify Dependencies` in the GUI. If packages are missing, install them into the portable interpreter as shown above.

Updating dependencies
---------------------
- Only install the runtime dependencies required by the active Qt GUI: `PySide6`, `pyserial`, `Pillow` (if charts/legacy GUI are used), `matplotlib` (optional for charts), `openpyxl` (optional for Excel export).

Where to find help
------------------
- See `PORTABLE_BUILD.md` and `INSTALLATION.md` for build and daily-use notes.
