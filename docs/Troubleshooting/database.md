# Database Troubleshooting

## Default location

    data/attendance.db

## Database access failure

Check that `data/` is writable and that another process is not replacing or holding the database.

The SQLite layer uses a 30-second connection timeout and enables foreign keys.

## Restore rejected

The selected backup must be:

- inside `data/backups/` after path resolution,
- a regular file,
- a `.db` file,
- a valid SQLite file with the expected magic header.

Symlink and sibling-prefix escapes are blocked.

## Unknown student rows

Fingerprint ID 0 is a reserved `Unregistered` placeholder. Real students use IDs 1–127.

## Deleted students and history

Deleting a student changes historical attendance references to ID 0 instead of deleting the attendance history.

## Wrong Time In / Time Out

Check `attendance.event_type` and `status`. The first qualifying scan is `time_in`; repeated scans are `scan` and do not mark departure. A real Time Out is a separate row with `event_type='time_out'` and `status='TIME OUT'`, created through the teacher/admin Record Time Out action. Legacy rows may still have automatic `time_out` tags from older releases; those tags alone are not proof that a student departed. Missing tags are backfilled during database initialization.

## Reports changed after restore

Reports and attendance evaluation read the live database. Restoring an older backup therefore changes subsequent results.
