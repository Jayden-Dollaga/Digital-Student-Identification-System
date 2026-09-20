# DSIS Logging Guide

DSIS uses a centralized Python logger shared by the web UI, serial layer, attendance processor, database layer, and runtime launcher.

## Log destinations

| Destination | Purpose |
| --- | --- |
| Console | Immediate runtime feedback and debugging |
| `data/logs/` | Per-run persistent logs when file logging is enabled |

Default per-run filename pattern:

`fingerprint_attendance_YYYYMMDD_HHMMSS.log`

## Configuration

Logging is controlled through `python/config.py` and persisted settings where exposed by the UI.

Important settings include:

- `log_to_file` — enable file output;
- `enable_debug_logging` — enable verbose DEBUG messages;
- log directory and file-name settings;
- log retention count.

The default retention behavior keeps the most recent **7** matching per-run files. Old files are pruned when a new logging session starts.

## Logger API

Core code uses the shared proxy:

```python
from core.logger import log

log.debug("Detailed diagnostic")
log.info("Normal lifecycle event")
log.success("Operation completed")
log.warning("Recoverable problem")
log.error("Operation failed")
log.critical("Severe failure")
```

The formatter includes a timestamp, log level, source category, and message. Structured key/value context may also be attached to a log entry.

## Source categories

| Source | Typical components |
| --- | --- |
| SERIAL | serial handler and device discovery |
| ATTENDANCE | attendance processing |
| DATABASE | SQLite and database operations |
| GUI | UI/worker components |
| SYSTEM | launcher/logger/runtime events |

## What is logged

Typical operational events include:

- application startup and shutdown;
- serial discovery, connection, disconnection, and reconnect attempts;
- device identity metadata and fingerprint-count activity;
- scan results and attendance writes;
- enrollment/delete/wipe progress and failures;
- database backup and restore results;
- permission-denied events;
- unexpected exceptions.

Passwords are not intended to be logged. Runtime logs should still be treated as sensitive operational data.

## Reconnect diagnostics

During intermittent serial failures, search for sequences such as:

```text
Attempting reconnect
Auto-reconnect attempt ... failed
Auto-reconnect successful
Auto-reconnect failed after ... attempts
```

The sequence helps distinguish a transient device disconnect from a persistent port, driver, or firmware problem.

## Backup and restore diagnostics

Successful backup and restore operations log their outcome and path. Restore messages are particularly important because restore replaces the active database.

Recommended support evidence:

1. the relevant timestamped log file;
2. the backup filename/path;
3. the COM port and firmware metadata;
4. the operation that was running when the failure occurred.

## Debug logging

Enable DEBUG logging only while investigating difficult issues. It can produce significantly more serial and reconnect detail.

After troubleshooting, disable debug output when it is no longer needed.

## Safe sharing

Before sending logs outside the project, review them for:

- student identifiers;
- machine-specific paths;
- COM-port/device information;
- database/backup filenames;
- other environment-specific details.

Logs should be redacted as appropriate before public issue reports.

Last reviewed: 2026-09-20.