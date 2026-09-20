# DSIS Testing and Validation

This document records the current documented validation state. Test results are point-in-time evidence; source code and active tests remain authoritative when behavior changes.

## Latest documented full run

The latest documented full repository test run in this file was executed against HEAD `d3fb362` on 2026-09-16 with Python 3.14.6:

| Result | Count |
| --- | ---: |
| Passed | 233 |
| Skipped | 3 |
| Failed | 1 |

The failing test was an attendance-export contract mismatch: `test_v3_today_export_uses_visible_fallback_rows` expects `Present`, while the current implementation returns the more specific `Early` status for that fixture.

Until that test and product contract are aligned, this documented run should not be described as fully green.

## Documented hardware validation

A physical ESP32/AS608 validation was recorded on 2026-09-09 using COM4. The test device identified itself as DSIS / ESP32 / AS608 with protocol 1.

Documented checks included:

- serial auto-discovery;
- device connection;
- fingerprint-count traffic;
- scan-mode entry/exit;
- enrollment cancellation;
- disconnect handling;
- empty-device wipe;
- deletion of an absent fingerprint ID.

These checks do not substitute for testing successful enrollment or successful attendance with a real fingerprint placed on the sensor.

## Firmware validation note

The maintained firmware validates a fingerprint template with `loadModel()` before `deleteModel()` so an absent fingerprint slot is less likely to be reported as a successful delete.

## Recommended software validation

```powershell
python -m pytest -q
python -m compileall python
node --check python/gui_web/web/app.js
```

## Targeted test groups

```powershell
python -m pytest tests/test_gui_web_smoke.py
python -m pytest tests/test_permissions_and_attendance_tagging.py
python -m pytest tests/test_database_features.py tests/test_database_reset.py tests/test_database_security.py
```

## Guarded hardware smoke test

```powershell
$env:DSIS_RUN_HARDWARE = "1"
$env:PYTHONPATH = "$PWD\python"
python -m pytest -q tests/physical_esp32_smoke.py
```

Run hardware tests only against an approved test device/data set. Do not perform destructive checks against production fingerprint templates or student records.

## Manual v3 acceptance

### Connection

- ESP32 appears as a Windows serial device;
- DSIS discovers or opens the intended port;
- `ID?` returns valid DSIS metadata;
- fingerprint count is reported.

### Scan

- SCAN enters scan mode;
- registered fingerprint events reach the application;
- confidence is displayed/classified correctly;
- repeated scans are subject to firmware and application cooldown;
- unknown scans use reserved ID 0 / `Unregistered`.

### Enrollment

- valid student fields are accepted;
- enrollment captures two fingerprint images;
- mismatched captures fail;
- cancellation returns to command mode;
- the student profile is saved only after device success.

### Delete

- delete requires the correct permission;
- `DELETE:<id>` is sent to the device;
- local profile deletion follows confirmed device success;
- failed device deletion does not silently remove the local profile.

### Wipe

- create a backup first;
- device `WIPE` is confirmed;
- linked local student/attendance cleanup is confirmed;
- fingerprint count refreshes;
- partial hardware/local cleanup failure is surfaced.

### Evaluation and reports

- day/week/month evaluation loads;
- distinct attendance dates are counted;
- category bands match the current UI;
- sorting works;
- authorized CSV export succeeds and contains the expected columns.

## Known test-process caveat

The historical documented run reported Windows process exit status `-1073740791` after pytest output, attributed in the existing notes to GUI/Qt teardown rather than an assertion failure. This should be retested against current HEAD before being treated as a current failure.

## Test scope boundaries

Software-only tests can verify parsing, permissions, database behavior, API contracts, and frontend syntax. They cannot prove physical fingerprint capture, sensor power stability, USB signal quality, or real template matching.

Legacy v1/v2 tests are retained for historical/reference coverage and do not establish that the v3 launcher is correct.

Last reviewed: 2026-09-20.