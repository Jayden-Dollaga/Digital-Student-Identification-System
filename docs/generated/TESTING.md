# Testing Audit

## Test coverage areas

The test suite in `tests/` covers the following areas:

- Serial and device discovery behavior
- Attendance processing and scan cooldown logic
- GUI page rendering and state transitions for the Qt UI
- Settings persistence and theme toggling
- Firmware helper candidate discovery and upload command generation
- VID/PID normalization and port scoring
- Database CRUD and reset operations

## Notable test files

- `test_attendance_processor.py` — attendance scan parsing and cooldown tests.
- `test_auto_port_probe.py` — serial discovery and probe heuristics.
- `test_firmware_helper.py` — firmware candidate discovery and upload command generation.
- `test_qt_attendance_page.py` — Qt attendance page tests.
- `test_qt_students_page.py` — Qt students page tests.
- `test_qt_settings_logs.py` — settings and logs integration in Qt.
- `test_serial_troubleshooting.py` — serial troubleshooting text and flow.
- `test_settings_persistence.py` — GUI settings store behavior.
- `test_vidpid_normalization.py` — low-level serial port normalization logic.

## Test environment

- The project includes `pytest.ini` for test configuration.
- Many tests appear to target the Qt stack and may require PySide6.
- Some tests are GUI-focused, suggesting both functional and regression coverage for the newer interface.

## Recommendations

- Add a dedicated test summary file under `docs/generated/` that maps tests to feature areas.
- Ensure headless test execution for key components by increasing coverage of core services outside the UI.
