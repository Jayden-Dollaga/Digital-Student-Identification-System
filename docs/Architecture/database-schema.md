# DSIS SQLite Database Schema

## Overview

DSIS uses a local SQLite database as the system of record for student profiles and attendance events.

The active implementation is `python/core/database.py`.

The database is created automatically when needed. Connections enable SQLite foreign-key enforcement and use a 30-second connection timeout.

Default path:

```text
data/attendance.db
```

## Entity model

```text
students
   │
   │ fingerprint_id
   │
   └──────────────< attendance
```

A student's AS608 template ID is the link between the physical device and the local student profile.

## students

```sql
CREATE TABLE students (
    fingerprint_id  INTEGER PRIMARY KEY,
    student_no      TEXT    NOT NULL UNIQUE,
    student_name    TEXT    NOT NULL,
    grade           TEXT    NOT NULL,
    section         TEXT    NOT NULL,
    enrollment_date TEXT    NOT NULL,
    updated_date    TEXT    NOT NULL
);
```

| Column | Type | Meaning |
| --- | --- | --- |
| `fingerprint_id` | INTEGER | AS608 template slot; normal student IDs are 1-127 |
| `student_no` | TEXT | Internal database field presented to users as **Student LRN** |
| `student_name` | TEXT | Student's display name |
| `grade` | TEXT | Grade/class level |
| `section` | TEXT | Section/class identifier |
| `enrollment_date` | TEXT | Enrollment timestamp |
| `updated_date` | TEXT | Last profile update timestamp |

Indexes:

- `idx_student_no` on `student_no`
- `idx_grade_section` on (`grade`, `section`)

## attendance

```sql
CREATE TABLE attendance (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint_id  INTEGER NOT NULL,
    date            TEXT    NOT NULL,
    time            TEXT    NOT NULL,
    confidence      INTEGER NOT NULL,
    status          TEXT    NOT NULL,
    timestamp       TEXT    NOT NULL,
    event_type      TEXT,
    FOREIGN KEY (fingerprint_id) REFERENCES students(fingerprint_id)
);
```

| Column | Meaning |
| --- | --- |
| `id` | Database event identifier |
| `fingerprint_id` | Fingerprint slot associated with the scan |
| `date` | Local calendar date |
| `time` | Local time shown in attendance records |
| `confidence` | AS608 match confidence supplied by the firmware |
| `status` | Application attendance/match classification |
| `timestamp` | Full timestamp used for event ordering |
| `event_type` | Explicit `time_in` / `time_out` tagging where assigned |

Indexes:

- `idx_attendance_fingerprint_id`
- `idx_attendance_date`
- `idx_attendance_timestamp`

## Reserved fingerprint ID 0

`fingerprint_id = 0` is reserved for the permanent `Unregistered` system row.

This row exists because the attendance table has a foreign key. Unknown scans can therefore be recorded without inventing a real student profile.

Normal student-management operations must use IDs 1-127 and must not treat ID 0 as an ordinary student.

## Validation

The database validates:

- fingerprint ID is an integer from 1 through 127 for real student records
- student number is required, unique, and limited to supported characters
- student name is required and supports Unicode letters plus safe punctuation
- grade and section are required and limited to supported characters and length

## Event tagging and migration

Older databases may have an attendance table without `event_type`.

During initialization, DSIS:

1. checks the existing attendance schema;
2. adds `event_type` when necessary;
3. backfills missing values using fingerprint ID and date ordering;
4. treats the first scan for a student/date as `time_in`;
5. treats subsequent scans on that same date as `time_out`.

The migration is intentionally conservative. It does not attempt to reconstruct arbitrary missing historical schema changes.

Back up the database before schema changes or upgrades.

## Deletion and foreign keys

Because attendance rows reference student fingerprint IDs, student deletion must be coordinated with attendance retention behavior in the application.

Device deletion and local record deletion are separate operations: the v3 UI sends a device delete command and updates the local profile only after the device reports successful deletion.

## Backups

Backup files are stored under:

```text
data/backups/
```

Restore is permission-gated and validates the selected backup path and `.db` extension before replacing the active database.

A restore is a replacement of the active database, not a merge.

## Reporting

Reports read from the live SQLite database.

Attendance Evaluation supports:

- Day
- Monday-Sunday Week
- Calendar Month

It counts distinct attendance dates for each student within the selected period.

## Data safety

The database is local and unencrypted at rest. Access to the Windows machine and runtime data directory should therefore be restricted appropriately.

Do not commit real student records or production database files to source control.

Last reviewed: 2026-09-20.
