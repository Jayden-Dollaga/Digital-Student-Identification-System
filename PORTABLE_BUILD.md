# Portable Windows Build

The current source application is the HTML/pywebview v3 interface. The
PyInstaller specification targets `run_web_gui.py` and bundles the V3 web
assets. The
specification is [DSIS.spec](DSIS.spec), and the build launcher is
[build_exe.bat](build_exe.bat).

## Build

From the repository root, run:

```text
build_exe.bat
```

The script invokes PyInstaller with `DSIS.spec` and writes the executable to:

```text
dist\DSIS\DSIS.exe
```

The build keeps `data/` external and writable. Copy the generated `dist\DSIS`
directory together with a writable `data/` directory when testing on another
machine; settings, the SQLite database, backups, charts, and logs must not be
written inside the bundled executable area.

## Historical Portable Workflow

The repository also retains `tools/build_portable.bat` and
`tools/fingerprint_portable.spec`. That workflow packages the older
CustomTkinter application and should be treated as compatibility tooling, not as
the supported Qt release build. `tools/portable_bootstrap.bat` installs the
requirements used by that portable setup.

The older CustomTkinter workflow remains compatibility tooling only. For current
source launches, use `run_web_gui.bat`. Verify any packaged build on a
disposable test machine before distribution.

## Validation

Before distributing a build:

1. Run `python run_web_gui.py` from the repository root as a source launch smoke test.
2. Run `build_exe.bat` and confirm `dist\DSIS\DSIS.exe` exists.
3. Confirm `dist\DSIS\_internal\gui_web\web\index.html`, `app.js`, and `styles.css` exist.
4. Test the executable on a clean Windows machine or USB copy.
5. Confirm serial connection, enrollment, attendance, backups, and database access.
6. Confirm `data\settings.json`, `data\attendance.db`, `data\backups`, and `data\logs` remain writable.

The source build was validated on 2026-09-09. Clean-machine, USB, and physical
ESP32 validation still require the target hardware/environment.

Last verified: 2026-09-09, source build and automated smoke checks.
