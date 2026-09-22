# Logging

The central logger lives in `python/core/logger.py`.

## Runtime logs

When file logging is enabled, logs are written under:

    data/logs/

The configured rotation defaults to a midnight boundary, one rotation interval, and seven retained backup files.

## What the application logs

Depending on log level and operation, the logger records:

- startup and shutdown,
- COM discovery and handshake results,
- reconnect attempts,
- serial errors,
- enrollment/delete/wipe progress,
- permission denials,
- database/report errors,
- backup/restore failures.

The v3 UI can mirror recent log messages and retrieve recent lines through `get_app_log`.

## Debug logging

`enable_debug_logging` enables verbose diagnostics. This can substantially increase log volume.

## Sensitive information

Treat `data/logs/` as sensitive operational data. Redact student information, local paths, or private diagnostics before sharing logs publicly.

## Maintenance

Changes to logging behavior should be reflected in the Troubleshooting and runtime-data documentation.
