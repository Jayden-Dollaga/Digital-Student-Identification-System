# Portable Windows Build

The current packaging workflow uses PyInstaller for the Qt interface. The
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

The spec packages `run_qt_gui.py`, the Qt stylesheets, and the declared hidden
imports. It excludes the legacy CustomTkinter modules from this build.

## Historical Portable Workflow

The repository also retains `tools/build_portable.bat` and
`tools/fingerprint_portable.spec`. That workflow packages the older
CustomTkinter application and should be treated as compatibility tooling, not as
the supported Qt release build. `tools/portable_bootstrap.bat` installs the
requirements used by that portable setup.

Use the Qt workflow above for current releases. Use the historical workflow only
when reproducing an older deployment, and verify its output on a disposable test
machine.

## Validation

Before distributing a build:

1. Run `python run_qt_gui.py` from the repository root as a source launch smoke test.
2. Run `build_exe.bat` and confirm `dist\DSIS\DSIS.exe` exists.
3. Test the executable on a clean Windows machine or USB copy.
4. Confirm serial connection, enrollment, attendance, and database access.

Clean-machine and USB validation have not been recorded in this document.

Last verified: 2026-09-03, against commit d68a405
