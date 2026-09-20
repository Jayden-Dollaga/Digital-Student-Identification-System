# DSIS SQLite Database Maintenance

This document describes the current database contract and maintenance rules for DSIS v3. The implementation is `python/core/database.py`.

## Database location

Default live database:

`data/attendance.db`

The database is SQLite; no database server is required. Connections enable foreign-key enforcement and use a 30-second timeout.

## Current schema

### students

| Column | Type | Constraints / meaning |
| --- | --- | --- |
| fingerprint_id | INTEGER | Primary key; real fingerprint IDs 1-127 |
| student_no | TEXT | Required, unique; displayed as Student LRN |
| student_name | TEXT | Required |
| grade | TEXT | Required |
| section | TEXT | Required |
| enrollment_date | TEXT | Enrollment timestamp |
| updated_date | TEXT | Last profile update timestamp |

Indexes: `idx_student_no` and `idx_grade_section`.

### attendance

| Column | Type | Meaning |
| --- | --- | --- |
| id | INTEGER | Autoincrement event ID |
| fingerprint_id | INTEGER | Foreign key to students |
| date | TEXT | Attendance date |
| time | TEXT | Attendance time |
| confidence | INTEGER | AS608 confidence supplied by firmware |
| status | TEXT | Application status/classification |
| timestamp | TEXT | Full event timestamp |
| event_type | TEXT | Optional explicit time_in/time_out tag |

Indexes: `idx_attendance_fingerprint_id`, `idx_attendance_date`, and `idx_attendance_timestamp`.

## Reserved fingerprint ID 0

`fingerprint_id = 0` is reserved for the permanent `Unregistered` system row. Unknown fingerprint events use this row so that the attendance foreign key remains valid.

Normal student validation does not allow ID 0 as a real student.

## Initialization and migration

`init_database()` creates missing tables and indexes, enables the attendance `event_type` migration, removes invalid non-positive legacy rows, and seeds the reserved ID 0 row when needed.

If an existing attendance table lacks `event_type`, DSIS adds the column and backfills older rows. The migration treats the first scan for a fingerprint on a date as `time_in` and later scans on that same date as `time_out` using deterministic ordering.

The migration is not a general-purpose schema repair system. Back up old databases before upgrading and verify a copy first.

## Validation

Student validation currently enforces:

- fingerprint ID 1-127 for real student records;
- Student LRN 1-50 characters using letters, numbers, dots, hyphens, and underscores;
- student name 1-100 characters with Unicode letters and safe punctuation;
- grade and section 1-50 characters using supported letters/numbers/spacing/punctuation.

The database layer also provides field-level validation feedback for the UI.

## Attendance writes

Registered scans write the fingerprint ID, confidence, application status, and timestamp to SQLite.

Unknown scans use ID 0 with the `Unregistered` profile.

The application attendance processor applies its per-fingerprint cooldown before calling the database writer.

## Student deletion

The v3 API coordinates physical fingerprint deletion with local record deletion. The ESP32 delete operation must report success before the linked local student profile is removed.

Device deletion and local deletion are therefore separate layers of the workflow, even though the UI presents them as one operation.

## Device wipe

Device wipe is coordinated by the v3 API: successful ESP32 `WIPE` is followed by local student/attendance cleanup. If local cleanup fails after hardware success, the API reports the partial state.

Create a database backup before wipe.

## Backups

Backups are timestamped SQLite snapshots stored under:

`data/backups/`

The active database remains the live source for reports. Backups are recovery snapshots and are not merged into the live database during normal operation.

## Restore

Restore is permission-gated. The API validates the selected backup location and supported `.db` format before replacing the live database.

Restore is a replacement, not a merge. Create a fresh backup before restoring.

## Reporting implications

Attendance Evaluation reads from the live attendance table and deduplicates dates per student for the selected Day, Monday-Sunday Week, or Month window.

The evaluation denominator is based on observed attendance activity in the selected range; it does not automatically count every empty calendar date.

## Maintenance commands

Recommended verification:

```powershell
python -m pytest tests/test_database_features.py tests/test_database_reset.py tests/test_database_security.py
```

Do not edit production SQLite files manually unless performing controlled maintenance. Prefer the application workflows or a verified migration procedure.

Last reviewed: 2026-09-20.