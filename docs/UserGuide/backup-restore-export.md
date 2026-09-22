# Backup, Restore and Export

## Database backups

Backups are SQLite filesystem copies created by `core.database.backup_database()`.

Filename:

    attendance_YYYYMMDD_HHMMSS.db

Location:

    data/backups/

Only files matching `attendance_*.db` are listed by the backup listing helper.

## Automatic backup

The API runs an automatic-backup worker after the pywebview window has been attached.

The default setting is 25 minutes between due-checks. A new backup is created when at least the configured minimum interval (24 hours in `auto_backup_if_needed()`) has elapsed since the latest backup.

The due-check is not a live database replica.

## Restore

Restore is restricted to the restore permission.

The selected path must:

1. resolve inside the runtime `data/backups/` directory,
2. remain inside that directory after symlink/path resolution,
3. exist as a regular file,
4. end in `.db`,
5. begin with the SQLite `SQLite format 3\0` header.

The validated file replaces `data/attendance.db`.

**Restore is replacement, not merge.**

Before restoring, operators should create a current backup if they need to preserve the present data.

## CSV exports

Current export surfaces include:

- attendance CSV,
- students CSV,
- attendance evaluation CSV,
- statistics report output.

CSV output uses UTF-8 with BOM for compatibility with spreadsheet programs and sanitizes cells against formula injection.

Export filenames include a timestamp.

Exports are operator-generated copies of data and should be handled as sensitive files.

## Charts and reports

Statistics/chart helpers can write artifacts into `data/charts/`.

Report generation reads the live database. It does not automatically read the most recent backup.

## Data safety

Do not commit:

- live `attendance.db`,
- `settings.json`,
- backup files,
- generated exports,
- logs.

Treat backups and exports with the same care as the live database.
