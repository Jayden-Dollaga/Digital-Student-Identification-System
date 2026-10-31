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

A dated **half-day class** is an explicit schedule override and counts as a school day even if it falls on a normally excluded weekend or recurring day off. Holiday and suspension entries still suppress attendance for that date.

The logic is centered around `core.attendance_status.py` and `core.attendance_calendar.py`.

## Status categories

Attendance status is evaluated using local script logic for whether the student arrived on time, arrived late, or missed the expected window. The categories are derived by the evaluation engine rather than from the serial device itself.

## Reports and exports

Attendance summaries count qualifying student-days, not the number of times a sensor was scanned. Repeated scans remain in the audit trail; they must not inflate daily presence totals or student rankings. Explicit Time Out events are shown separately and are not an additional attendance day.

The Reports page supports today's attendance, a selected calendar week, the last 30 days, and a custom date range. Custom exports require both dates, reject an end date before the start date, and are limited to 367 inclusive calendar days per file. Evaluation reports use the selected Day, Week, or Month period and the configured school calendar.

A missing qualifying scan is not proof of absence by itself. If the device or connection was unavailable, review connection logs and school records before using an evaluation for disciplinary decisions.
