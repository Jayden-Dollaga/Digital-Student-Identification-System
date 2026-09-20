# DSIS Release Guide

> Release documentation is authoritative only for a tagged or explicitly named commit. The current repository may contain unreleased v3 work; do not describe `main` as a published v3 release without a tag and validated artifact.

## Versioning

Use a version tag in the form `vMAJOR.MINOR.PATCH`. Update `docs/Development/change-log.md` before tagging, moving the verified unreleased entries under the new version heading. Keep `SECURITY.md`, build documentation, and release notes on the same supported release line.

## Release checklist

1. Start from a clean `main` branch and confirm the working tree contains no runtime data or build artifacts.
2. Run `python -m pytest -q`, `python -m compileall python`, and `node --check python/gui_web/web/app.js`.
3. Build the Windows package using the documented PyInstaller process in `PORTABLE_BUILD.md`.
4. Validate the package on a clean Windows machine with the required Python/runtime files and the correct USB serial driver installed.
5. Verify the maintained firmware sketch, ESP32 board selection, AS608 wiring, and host handshake at 115200 baud.
6. Record the firmware sketch and commit in the release notes. Do not publish `firmware/prebuilt/attendance_v1.0.bin` as a usable image; it is a placeholder.
7. Verify the README, installation, API, architecture, hardware, troubleshooting, and security documentation describe the same release behavior.
8. Tag the release and publish the generated artifact together with installation and troubleshooting links.

Hardware validation is required for serial or firmware changes but may be documented as unavailable for documentation-only releases.
