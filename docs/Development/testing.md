# Testing and Validation

## Static and automated checks

Run the current repository checks:

    python -m pytest -q
    python -m compileall python
    node --check python/gui_web/web/app.js

## Important behavior tests

| Test | What it documents |
| --- | --- |
| `tests/test_v3_authentication.py` | password hashing, first-run, role hierarchy, wrong password, session lock/expiry |
| `tests/test_attendance_processor.py` | serial attendance parsing and cooldown |
| `tests/test_attendance_status.py` | Early/Present/Late/Absent/Out boundaries and half-days |
| `tests/test_permissions_and_attendance_tagging.py` | permission enforcement and explicit time-in/time-out tagging |
| `tests/test_database_security.py` | backup-path containment and SQLite validation |
| `tests/test_database_reset.py` | local wipe behavior |
| `tests/test_settings_persistence.py` | settings round-trip and merge |
| `tests/test_settings_toggles.py` | setting defaults/types/persistence |
| `tests/test_gui_shutdown.py` | GUI shutdown behavior |
| `tests/test_sensor_failure_handshake_recovery.py` | boot identity discovery when sensor initialization fails |
| `tests/test_serial_monitor_boot_banner.py` | serial boot output handling |
| `tests/test_serial_troubleshooting.py` | connection diagnostics |
| `tests/test_gui_web_smoke.py` | v3 web UI smoke behavior |
| `tests/test_mode_exclusivity.py` | scan/enrollment mode exclusivity |
| `tests/test_error_message_sanitization.py` | safe error-message behavior |

## Hardware-dependent checks

Automated unit tests cannot replace physical checks for:

- ESP32 USB enumeration and Windows drivers,
- real AS608 communication,
- fingerprint enrollment/matching,
- firmware wipe,
- physical cable/device interruption and reconnect,
- packaged executable on a clean Windows machine.

Record those separately from the automated suite.

## Release validation

A release candidate should pass the three source checks, the PyInstaller build, and physical validation whenever the change affects serial, firmware, or device workflows.
