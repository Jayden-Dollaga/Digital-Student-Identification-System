# Release Guide

This project is released from the maintained v3 app and its matching firmware. A release is only valid when the source, firmware, package, and documentation describe the same product boundary.

> A repo snapshot without a clear tag and a tested package should be treated as unreleased work, not a published release.

## Release checklist

- Confirm the work is on the intended branch and the tree is clean.
- Run the validation commands:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q
python -m compileall python
node --check python/gui_web/web/app.js
```

- Validate the maintained firmware at `firmware/ESP32_DSIS_AllInOne/ESP32_DSIS_AllInOne.ino` on the target hardware.
- Verify the app launches from the repo root using `python run_web_gui.py`.
- Build the Windows package with the v3 PyInstaller spec in `Build/DSIS_v3.spec`.
- Confirm the packaged app works on a clean Windows machine with the proper USB driver.
- Verify `data/` remains writable and separate from the bundled executable.
- Update the changelog and relevant docs to reflect the exact release contents.
- Tag the release and publish the built artifact with installation and troubleshooting references.

## Release notes expectations

A release note should state:

- whether the app is the v3 pywebview build or a legacy UI build
- the firmware sketch and board target used for validation
- any hardware issues or required driver steps
- whether the release includes database or schema changes
- the exact validation commands and results

## Current support model

- Active product: DSIS v3 webview desktop app
- Active firmware: ESP32 DSIS all-in-one sketch
- Archived product: v1/v2 GUI implementations

See [docs/Development/change-log.md](docs/Development/change-log.md), [docs/Development/release-and-portable-build.md](docs/Development/release-and-portable-build.md), and [PORTABLE_BUILD.md](PORTABLE_BUILD.md) for implementation details.
