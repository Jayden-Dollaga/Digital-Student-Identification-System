# DSIS Portable Python

This guide describes the optional isolated Python runtime for development, testing, and source launches of the maintained DSIS v3 webview application.

## Purpose

Portable Python is useful when you want DSIS to use a project-local interpreter rather than the system Python installation.

It does **not** replace the packaged PyInstaller build described in [Portable Windows Build](../../PORTABLE_BUILD.md).

## Expected layout

Place a portable/full Python distribution here:

```text
system/python/python.exe
```

The repository does not include the Python runtime itself.

Some official embeddable Python distributions do not include pip. Before installing dependencies, verify:

```powershell
system\python\python.exe -m pip --version
```

If pip is unavailable, use a distribution that provides pip or provision it using the appropriate Python packaging procedure.

## Install dependencies

From the repository root:

```powershell
system\python\python.exe -m pip install -r requirements.txt
```

The runtime must include the dependencies required by the active v3 interface, especially pywebview and pyserial, plus the reporting/database/export dependencies in the repository requirements.

PySide6 and CustomTkinter remain in requirements because the repository preserves v2/v1 compatibility tests and historical tooling. They are not the current v3 UI stack.

## Launch the active application

```powershell
system\python\python.exe run_web_gui.py
```

No HTTP server is required. pywebview loads the local HTML interface into a native window.

## Runtime data

Portable Python does not relocate DSIS application data into the Python installation.

The application continues to use its configured runtime paths, including:

- `data/attendance.db`
- `data/settings.json`
- `data/backups/`
- `data/logs/`
- `data/charts/`
- `data/exports/`

Keep these writable and protect production data.

## Runtime manager

`tools/runtime_manager.py` can detect the portable interpreter, verify dependencies, launch the application, and execute tests.

Use the runtime manager for convenience; the maintained application itself remains `run_web_gui.py`.

## Testing

Software-only validation:

```powershell
system\python\python.exe -m pytest -q
system\python\python.exe -m compileall python
```

Frontend syntax:

```powershell
node --check python/gui_web/web/app.js
```

Physical fingerprint workflows still require the documented ESP32/AS608 hardware.

## Troubleshooting

### pip unavailable

The selected Python distribution may be an embeddable runtime without pip. Use a portable distribution that includes pip or provision pip.

### Native package installation fails

pywebview and GUI-related packages may require Windows-native dependencies. Review the error from pip rather than assuming the portable interpreter is incompatible.

### Serial device not found

Portable Python does not install USB drivers. Install the Windows driver for the ESP32 board's USB interface and verify the COM port in Device Manager.

### Different COM port

Windows can assign a new COM number on another machine or USB port. DSIS can auto-detect the device rather than relying on a persisted port.

## Related documentation

- [Installation](../../INSTALLATION.md)
- [Portable Windows Build](../../PORTABLE_BUILD.md)
- [v3 Workflows](../UserGuide/v3-workflows.md)
- [Tools Catalog](tools-catalog.md)

Last reviewed: 2026-09-20.
