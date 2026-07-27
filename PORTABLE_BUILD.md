# Portable build plan

## Goal

Build a portable Windows deployment that can run on another computer without requiring a separate Python installation.

## Current approach

1. Use PyInstaller to package the GUI entry point.
2. Bundle the application files and data folders into a single folder.
3. Keep a bootstrap script for machines that still need dependencies.
4. Test the build from a USB drive on a clean Windows machine.

## Planned steps

- Add a PyInstaller spec file.
- Package the GUI entry point from python/gui/app.py.
- Include the data folder and required assets.
- Use `tools\build_portable.bat` to build the distributable.
- Verify startup on a clean Windows machine.
- Keep a rollback copy of the last working build.

## Build steps

1. Open a command prompt.
2. Run `tools\build_portable.bat`.
3. After a successful build, launch the app from `dist\FingerprintAttendanceSystem`.
4. Test on another PC without a Python installation.
