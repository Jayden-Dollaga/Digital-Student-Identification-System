# Database Audit

> Point-in-time generated report. The active schema is documented in [database-schema.md](../Architecture/database-schema.md) and implemented in `python/core/database.py`.

## Storage backend

- SQLite is the primary data store.
- Default database file: `data/attendance.db`.
- The Python app initializes and interacts with the database via `python/core/database.py`.

## Schema overview

The code defines two main tables:

- `students`
  - `id`: auto-increment primary key.
  - `fingerprint_id`: integer fingerprint template ID.
  - `student_no`: student or enrollment number.
  - `student_name`: full name.
  - `grade`: grade level.
  - `section`: section or class.
  - `created_at`: timestamp of record creation.

- `attendance`
  - `id`: auto-increment primary key.
  - `fingerprint_id`: referenced fingerprint ID.
  - `date`: date string for the scan.
  - `time`: time string for the scan.
  - `confidence`: match confidence score.
  - `status`: scan status or match quality.
  - `timestamp`: ISO timestamp for audit and ordering.

## Key database behaviors

- `init_database()` ensures tables exist.
- `register_student()` inserts or updates a student profile.
- `delete_student()` removes a student by fingerprint ID.
- `log_attendance()` records scan events.
- `get_attendance_today()` and `get_attendance_all()` retrieve attendance rows.
- `get_daily_attendance_summary()` creates simplified in/out summaries by student and date.
- `clear_all_data()` wipes both student and attendance data.

## Reporting support

- `generate_statistics_report()` builds a text summary with totals, top students, and grade stats.
- Export helpers exist in `python/services/excel_export.py` for Excel output.

## Backup and restore

- Backups are managed in `python/services/backup.py`.
- The system supports database snapshots and restore operations.

## Observations

- Database functions are carefully wrapped with connection handling and `try/finally` cleanup.
- There are dedicated queries for statistics, paginated attendance, and student groupings.
- The code supports grade/section filtering and student join queries for attendance lookups.
