# Testing Results

The latest full test run was executed on 2026-09-09 with Python 3.14.6:

- 206 tests passed
- 1 test was skipped
- The suite includes database, security, serial, Qt-reference, webview smoke, permissions, enrollment, and UI tests.

## Run the tests

From the repository root:

```powershell
python -m pytest -q --disable-warnings
```

For the webview-specific smoke tests:

```powershell
python -m pytest tests/test_gui_web_smoke.py
```

## Manual v3 acceptance

The maintained interface is launched with `run_web_gui.bat` or `python run_web_gui.py`. With an ESP32 and AS608 connected, verify:

1. Connect and confirm the port, baud rate, device metadata, and fingerprint count.
2. Start and stop scanning and confirm the device mode and scan button agree.
3. Scan a registered fingerprint and confirm the attendance row and dashboard counts update.
4. Scan an unknown fingerprint and confirm it is shown as `Unregistered` and persisted through reserved `fingerprint_id = 0`.
5. Start, cancel, and complete enrollment; save the student only after device success is reported.
6. Delete a student and confirm the local profile is removed only after device deletion succeeds.
7. Wipe device fingerprints and confirm the device count reaches zero while student records remain.
8. Disconnect and reconnect and confirm pending operations clear and the count refreshes.

Prototype and archived Qt/CustomTkinter tests do not replace hardware validation. Physical ESP32 behavior still requires the documented board, sensor wiring, USB driver, and a connected device.

Last reviewed: 2026-09-09, against commit `ea3ea7c`.
