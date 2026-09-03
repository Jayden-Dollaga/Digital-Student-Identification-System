# Contributing to DSIS

## Branches and pull requests

- `main` is the integration branch.
- Create a short-lived feature or fix branch from the current `main`.
- Open a pull request before merging. Describe user-visible changes, firmware assumptions, and hardware used for testing.
- Do not commit runtime databases, logs, backups, build output, or local settings.

## Commits

Use an imperative subject with a simple category when useful, for example `Docs: clarify CP210x setup` or `Fix: handle serial reconnect`. Keep each commit focused and explain behavior changes in the body when the subject is not sufficient.

Documentation changes should update the relevant changelog entry. Do not rewrite published history; amend only a local, unpublished commit before opening a pull request.

## Validation

Before opening a pull request:

```powershell
python -m pytest
python -m compileall python
```

For hardware changes, also record the ESP32 board, USB bridge, sensor module revision, firmware sketch, and whether the host handshake succeeded at 115200 baud. The internal AS608 UART is 57600 baud and is not a host setting.

## Documentation source of truth

The maintained desktop interface is the PySide6/Qt application launched by `run_qt_gui.bat`. The all-in-one firmware at `firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino` is the supported firmware path. Historical sketches and the placeholder binary are retained for reference and should not be presented as interchangeable installation options.
