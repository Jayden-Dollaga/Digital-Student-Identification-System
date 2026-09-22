# Attendance Rules

Attendance processing is defined by the current backend logic and the school calendar and schedule rules stored in `settings.json`.

## Confidence and cooldown

The app enforces:

- a configured `min_confidence` threshold,
- a cooldown window between scans for the same fingerprint ID,
- a device-level and desktop-level interpretation of the same match events.

The actual values are loaded from configuration and can be overridden through settings.

## Event types

Attendance rows may carry `event_type` values such as:

- `time_in`
- `time_out`

These are derived during database migration and are used when evaluating attendance status and transitions.

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
