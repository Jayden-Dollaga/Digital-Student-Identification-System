# DSIS Release Guide

## Versioning

Use a version tag in the form `vMAJOR.MINOR.PATCH`. Update `docs/Development/change-log.md` before tagging, moving the verified unreleased entries under the new version heading. Keep `SECURITY.md`, build documentation, and release notes on the same supported release line.

## Release checklist

1. Start from a clean `main` branch and confirm the working tree contains no runtime data or build artifacts.
2. Run `python -m pytest` and `python -m compileall python`.
3. Build the Windows package using the documented PyInstaller process in `PORTABLE_BUILD.md`.
4. Validate the package on a clean Windows machine with the required Python/runtime files and the correct USB serial driver installed.
5. Verify the maintained firmware sketch, ESP32 board selection, AS608 wiring, and host handshake at 115200 baud.
6. Record the firmware sketch and commit in the release notes. Do not publish `firmware/prebuilt/attendance_v1.0.bin` as a usable image; it is a placeholder.
7. Tag the release and publish the generated artifact together with installation and troubleshooting links.

Hardware validation is required for serial or firmware changes but may be documented as unavailable for documentation-only releases.
