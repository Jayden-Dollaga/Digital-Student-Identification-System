# Portable Python for DSIS

This document describes the optional isolated Python runtime for development, testing, and source launches of the active v3 webview application.

## Layout

Place a portable Python distribution under `system/python/` so the interpreter is available at `system/python/python.exe` on Windows. The repository does not include the runtime itself.

The official embeddable Python distribution may not include `pip`. Use a full portable distribution with pip, or provision pip before installing project dependencies. Confirm that this command works before continuing:

```powershell
system\python\python.exe -m pip --version
```

## Install and launch

From the repository root:

```powershell
system\python\python.exe -m pip install -r requirements.txt
system\python\python.exe run_web_gui.py
```

`tools/runtime_manager.py` can detect the portable interpreter, verify dependencies, launch the application, and run tests. The active application is `run_web_gui.py`; the former Qt and CustomTkinter interfaces are archived.

## Dependencies

The active webview interface requires `pywebview`, `pyserial`, and the packages listed in `requirements.txt` for database, reporting, and export features. `PySide6` and `customtkinter` are only needed for archived interfaces or historical tests.

Hardware is not required for basic software validation, but serial behavior and fingerprint workflows require a connected ESP32 and AS608 sensor.

## Related guides

- [Portable Windows Build](../../PORTABLE_BUILD.md)
- [Installation](../../INSTALLATION.md)
- [Testing results](../UserGuide/testing-results.md)
