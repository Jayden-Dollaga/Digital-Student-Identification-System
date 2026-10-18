# Attendance Rules

Attendance processing is defined by the current backend logic and the school calendar and schedule rules stored in `settings.json`.

## Confidence and cooldown

The app enforces:

- a configured `min_confidence` threshold,
- a cooldown window between scans for the same fingerprint ID,
- a device-level and desktop-level interpretation of the same match events.

The actual values are loaded from configuration and can be overridden through settings.

## Event types

Attendance rows may carry these `event_type` values:

- `time_in` — the first qualifying scan of the day records arrival.
- `scan` — a later qualifying scan. It remains in the audit trail but does not imply departure.
- `time_out` — an explicit departure action recorded by a teacher or administrator.

The Student Details panel provides **Record Time Out**. A qualifying Time In must already exist, and a second Time Out for the same student/date is rejected. Old rows that were automatically tagged `time_out` by earlier versions are treated as historical scan events unless their status is the explicit `TIME OUT` marker.

The configured Time Out schedule is used for schedule policy and reporting, but passing that time does not prove that a particular student left. A school should define who is authorized to record departures and whether manual correction/audit procedures are required.

## Schedule logic

The app understands:

- school time windows (`time_in`, `time_out`),
- early/late thresholds,
- half-day calendar exceptions,
- holiday and suspension days,
- school-day exclusions.

The logic is centered around `core.attendance_status.py` and `core.attendance_calendar.py`.

## Status categories

Attendance status is evaluated using local script logic for whether the student arrived on time, arrived late, or missed the expected window. The categories are derived by the evaluation engine rather than from the serial device itself.
