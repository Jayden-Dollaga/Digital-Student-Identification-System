# Testing Results

The latest full test run was executed on 2026-09-09 with Python 3.14.6:

- 204 tests passed
- 2 tests were skipped
- 4 prototype tests failed during database initialization

The passing suite covers database, security, serial, Qt-reference, webview smoke, permissions, enrollment, reporting, and UI behavior.

## Known failure

The four failures are `ActualUIPrototypeTest` and `CombinedUITest` cases. They fail in `python/core/database.py::init_database()` when an existing database contains attendance rows referencing the reserved `fingerprint_id = 0` row. The initializer attempts to delete non-positive student rows before recreating the reserved row, so SQLite foreign-key enforcement can reject that cleanup. This is an implementation/migration issue, not a documentation-only failure; the prototype tests should remain marked failing until the cleanup order or migration strategy is corrected.

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
3. Scan a registered fingerprint and confirm the attendance row and dashboard count update.
4. Scan an unknown fingerprint and confirm it is shown as `Unregistered` and persisted through reserved `fingerprint_id = 0`.
5. Open Attendance Evaluation, switch between day, week, and month, and confirm rates use observed attendance dates rather than every calendar day.
6. Export the selected evaluation as CSV and confirm the output contains student, presence, absence, rate, and category columns.
7. Start, cancel, and complete enrollment; save the student only after device success is reported.
8. Delete a student and confirm the local profile is removed only after device deletion succeeds.
9. Wipe device fingerprints and confirm the device count reaches zero while student records remain.
10. Disconnect and reconnect and confirm pending operations clear and the count refreshes.

Prototype and archived Qt/CustomTkinter tests do not replace hardware validation. Physical ESP32 behavior still requires the documented board, sensor wiring, USB driver, and a connected device.

Last reviewed: 2026-09-09, against commit `e450433`.
