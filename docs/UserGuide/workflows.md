# Operator Workflows

This page captures the practical flow for running DSIS on a typical Windows workstation.

## Daily workflow

1. Connect the ESP32 to the PC using a data-capable USB cable.
2. Start the app with `run_web_gui.bat` or `python run_web_gui.py`.
3. Complete the first-run setup if no password is configured.
4. Connect to the device and confirm the handshake succeeds.
5. Enroll students.
6. Start scan mode.
7. Process attendance events.
8. Review dashboards and reports.
9. Create backups as needed.

## Enrollment workflow

- Use the student form to create or edit a student record.
- The fingerprint ID is tied to the actual AS608 sensor slot.
- Save the record only after the enrollment flow succeeds.
- If the device reports an enrollment failure, ensure the sensor is ready and no conflicting record exists.

## Attendance workflow

- Device scan events are interpreted by `AttendanceProcessor`.
- Known matches are logged and reported as attendance entries.
- Unknown or weak-match events are treated according to the configured confidence and cooldown rules.
- The application can evaluate attendance by day, week, or month depending on the report context.

## Backup and restore workflow

- The app can generate a DB backup from the UI or API layer.
- Snapshots are placed in `data/backups/`.
- Restore actions replace the current database with the selected backup.
- Follow normal operational caution before restoring historical data.
