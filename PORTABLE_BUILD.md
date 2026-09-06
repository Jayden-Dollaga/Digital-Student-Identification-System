# Portable Windows Build

The current source application is the HTML/pywebview v3 interface. The existing
PyInstaller specification still targets the former Qt interface and must be
updated before it can produce a current v3 release. The
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

The spec currently packages the historical `run_qt_gui.py` entry point and Qt
assets, which are no longer present in the active root tree. Do not describe its
output as the current v3 release until the spec is migrated to `run_web_gui.py`
and the pywebview assets.

## Historical Portable Workflow

The repository also retains `tools/build_portable.bat` and
`tools/fingerprint_portable.spec`. That workflow packages the older
CustomTkinter application and should be treated as compatibility tooling, not as
the supported Qt release build. `tools/portable_bootstrap.bat` installs the
requirements used by that portable setup.

Treat the existing PyInstaller workflow as historical until it is migrated. For
current source launches, use `run_web_gui.bat`. Verify any packaged build on a
disposable test machine before distribution.

## Validation

Before distributing a build:

1. Run `python run_web_gui.py` from the repository root as a source launch smoke test.
2. Run `build_exe.bat` and confirm `dist\DSIS\DSIS.exe` exists.
3. Test the executable on a clean Windows machine or USB copy.
4. Confirm serial connection, enrollment, attendance, and database access.

Clean-machine and USB validation have not been recorded in this document.

Last verified: 2026-09-06, against commit 6b44ca8
