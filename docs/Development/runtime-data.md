# DSIS Runtime Data

The `data/` directory contains local application state and generated runtime output. It is not source code and should normally remain outside commits and packaged executable internals.

## Runtime layout

| Path | Contents | Role |
| --- | --- | --- |
| `data/attendance.db` | Students and attendance events | Live SQLite source of record |
| `data/settings.json` | Preferences, setup state, authentication record | Persistent application configuration |
| `data/backups/` | Timestamped SQLite snapshots | Recovery/restore source |
| `data/logs/` | Per-run log files | Diagnostics and audit trail |
| `data/charts/` | Generated chart images | Regenerable reporting output |
| `data/exports/` | Generated CSV/report files | User output |

The application creates missing runtime directories as needed.

## Database

`data/attendance.db` is the live database for students and attendance.

Important properties:

- SQLite, no separate database server;
- foreign-key enforcement is enabled;
- normal fingerprint IDs are 1-127;
- fingerprint ID 0 is reserved for `Unregistered` unknown scans;
- attendance rows can carry confidence, status, timestamp, and time-in/time-out event type.

See [Database Maintenance](database-updates.md) and [Database Schema](../Architecture/database-schema.md).

## Settings

`data/settings.json` stores local configuration such as COM port, baud rate, theme, cooldown, confidence threshold, auto-detection, reconnect, logging, backup interval, attendance schedule, calendar exceptions, school name, and first-run progress.

The authentication record contains the password salt/hash and iteration count. The persisted `current_role` value is for UI continuity, not backend authorization.

## Backups

Backups are snapshots of the live SQLite database.

Default location:

```text
data/backups/
```

Restore replaces the active database; it does not merge records.

Create a fresh backup before destructive maintenance, schema changes, or restore.

## Logs

File logging is enabled by default in the current configuration.

Per-run files use a pattern similar to:

```text
fingerprint_attendance_YYYYMMDD_HHMMSS.log
```

The logger keeps the most recent configured number of run files; the default retention count is 7.

Logs may contain operational details and should be treated as sensitive when they reference real deployments.

## Charts and exports

Charts are generated output and can be recreated from application data.

CSV/report files are user-generated output. The application sanitizes spreadsheet formula-triggering content during export.

## Data retention

The current implementation does not provide an automatic attendance-record deletion schedule. Attendance history remains until an authorized application/database maintenance operation removes it.

Log retention is different: old per-run log files are automatically pruned according to logger retention settings.

## Security properties

DSIS does **not** claim encryption at rest.

Administrators should protect:

- the Windows account and machine running DSIS;
- `data/attendance.db`;
- `data/settings.json`;
- backup files;
- log files.

Do not commit real student data, production databases, passwords, fingerprint data, or private logs.

## Portability

Machine-specific state can become stale when a data directory is moved to another computer. In particular, the saved COM port may no longer exist. DSIS can detect a stale saved port and fall back to device discovery.

## Source references

- `python/settings_store.py`
- `python/core/database.py`
- `python/core/logger.py`
- `python/config.py`

Last reviewed: 2026-09-20.