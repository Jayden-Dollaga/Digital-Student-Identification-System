# Testing Results

The latest full test run was executed against HEAD `aa457e0` on 2026-09-11 with Python 3.14.6:

- 234 tests passed
- 1 test was skipped
- 2 web-shell tests failed

The passing suite covers database, security, serial, Qt-reference, webview smoke, permissions, enrollment, reporting, and UI behavior.

## Known refactor regressions

The latest web UI refactor removed the `deleteSelectedStudents` batch-delete function and the `student-status-today` element, but `tests/test_gui_web_smoke.py` still expects both symbols. The failures are:

- `test_v3_web_shell_contains_all_primary_workflows`
- `test_v3_web_bundle_uses_native_unicode_display_values`

These are current implementation/test-contract mismatches, not documentation failures. They should be resolved by either restoring the workflows/elements or updating the tests to the intentionally changed v3 contract.

## Test-process caveat

The Windows process exits with status `-1073740791` after pytest reports completion. This appears to occur during GUI/Qt teardown rather than during a test assertion. CI should continue investigating the non-zero post-test process exit.

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

Last reviewed: 2026-09-11, against commit `aa457e0`.
