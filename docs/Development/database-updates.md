# SQLite Database Updates

This document describes the current database contract. The active implementation is in `python/core/database.py`.

## Current schema

`students` uses `fingerprint_id` as its primary key and stores `student_no`, `student_name`, `grade`, `section`, `enrollment_date`, and `updated_date`.

`attendance` stores `id`, `fingerprint_id`, `date`, `time`, `confidence`, `status`, `timestamp`, and nullable `event_type`. Attendance rows reference `students(fingerprint_id)` through a foreign key, and database connections enable foreign-key enforcement.

## Initialization and migration

`init_database()` creates missing tables and indexes. Existing attendance tables receive the `event_type` column when it is absent, and legacy rows are backfilled with time-in/time-out values where possible.

The initializer does not reconstruct every possible missing legacy column. Existing databases should be backed up before an upgrade, and schema changes should be verified against a copy before deployment.

## Attendance constraints

Attendance writes must use an enrolled fingerprint ID. `fingerprint_id = 0` is not a valid unknown-scan record because no student with that key exists. Unknown scans may be handled by the UI or processor, but they are not a supported persisted attendance row under the current schema.

## Backup and restore

Database backups are stored under `data/backups/`. Restore operations validate that the selected file is inside that directory, exists, and has a `.db` extension. Create a backup before destructive operations or schema changes.

## Validation

Run the database and security tests from the repository root:

```powershell
python -m pytest tests/test_database_features.py tests/test_database_reset.py tests/test_database_security.py
```

Last reviewed: 2026-09-03, against commit `d68a405`.
