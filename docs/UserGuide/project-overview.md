# DSIS Project Overview

## Identity

**Digital Student Identification System (DSIS)** is a local Windows application for student identification and attendance using an ESP32 controller and AS608 fingerprint sensor.

Current maintained generation: **v3**.

Current desktop stack: **Python + HTML/CSS/JavaScript + pywebview**.

Current persistent storage: **SQLite + local JSON settings**.

## What DSIS does

DSIS covers the operational attendance lifecycle:

```text
Student enrollment
      ↓
Fingerprint template stored in AS608
      ↓
Student profile linked to fingerprint ID
      ↓
Fingerprint scan
      ↓
Attendance event
      ↓
SQLite persistence
      ↓
Dashboard / Attendance / Reports
      ↓
Day / Week / Month evaluation + CSV export
```

The application also provides device discovery, serial diagnostics, settings, role-based actions, database backup/restore, logs, and calendar-based attendance configuration.

## Current runtime

The supported launcher is `run_web_gui.py` or `run_web_gui.bat`.

`python/gui_web/main_web.py` creates the native pywebview window. `python/gui_web/api.py` exposes the Python application to JavaScript. The frontend is under `python/gui_web/web/`.

No local web server is required for the normal application.

## Hardware

| Component | Role |
| --- | --- |
| ESP32 WROOM-32 | Device controller and PC serial endpoint |
| AS608 | Fingerprint capture, model creation, search, delete, wipe |
| Windows PC | Runs DSIS and stores local data |
| USB connection | PC ↔ ESP32 power and serial transport |

Verified signal arrangement:

| Connection | Configuration |
| --- | --- |
| PC ↔ ESP32 | 115200 baud |
| ESP32 ↔ AS608 | UART2, 57600 baud |
| AS608 TX → ESP32 | GPIO14 |
| AS608 RX → ESP32 | GPIO27 |

See [Hardware Connections](../Hardware/hardware-connections.md) and [Wiring](../Hardware/wiring.md).

## Software architecture

The Python implementation is divided into focused responsibilities:

| Component | Responsibility |
| --- | --- |
| `core/device_discovery.py` | Port ranking and DSIS identity handshake |
| `core/serial_handler.py` | Serial connection, buffering, reconnect |
| `core/attendance.py` | Scan parsing, cooldown, confidence classification |
| `core/attendance_status.py` | Time-based attendance status |
| `core/attendance_calendar.py` | Holiday/suspension/half-day schedule rules |
| `core/database.py` | SQLite, reports, backups, restore, charts |
| `core/auth.py` | Password hashing and verification |
| `core/permissions.py` | In-memory role authorization |
| `core/logger.py` | Console/file logging |
| `gui_web/api.py` | UI/backend bridge |

## Student data model

The user-facing identifier is **Student LRN**. The database field remains `student_no` for compatibility.

A normal student record contains:

- fingerprint ID;
- Student LRN (`student_no`);
- full name;
- grade;
- section;
- enrollment timestamp;
- update timestamp.

Normal fingerprint IDs are 1-127. Fingerprint ID 0 is reserved for the `Unregistered` system row used by unknown scans.

## Attendance model

Attendance rows record:

- fingerprint ID;
- date;
- time;
- confidence;
- status;
- full timestamp;
- event type when assigned.

Older databases can be migrated to add the `event_type` field. The migration backfills legacy rows so the first scan for a fingerprint/date is `time_in` and later scans are `time_out`.

## Scan confidence and duplicate handling

The firmware's hardware-level match floor is 50 confidence.

The Python application uses a configurable default threshold of 100 for status classification:

| Score | Application status |
| ---: | --- |
| >= 100 | `GOOD MATCH` |
| 50-99 | `WEAK MATCH` |

A weak match is currently still stored by the Python attendance processor. The application threshold is not a second rejection gate.

Duplicate protection is provided by both the firmware's approximately 2-second post-scan delay and the application's default 10-second per-fingerprint cooldown.

## Attendance evaluation

Evaluation supports Day, Monday-Sunday Week, and Calendar Month.

Each student's result includes days present, days absent, attendance rate, and a category:

| Rate | Category |
| ---: | --- |
| 90-100% | Excellent |
| 75-89% | Good |
| 50-74% | Needs attention |
| below 50% | Low attendance |

The denominator uses observed attendance dates in the selected range. A date with no attendance activity is not automatically treated as a school day by this evaluation.

## Roles

Default role permissions:

| Role | Permissions |
| --- | --- |
| Administrator | scan, enroll, delete, wipe, export, backup, restore, attendance evaluation, calendar management |
| Teacher | scan, export, backup, attendance evaluation |
| Guest | scan, attendance evaluation |

Non-guest authenticated sessions expire after 600 seconds of inactivity by default.

The persisted `current_role` value in `data/settings.json` is for UI continuity. Backend authorization uses the in-memory session role.

## Authentication

There is no built-in default administrator password.

First-run password creation requires at least 8 characters. The authentication implementation uses PBKDF2-HMAC-SHA256 with a random 16-byte salt and 310,000 iterations.

## Settings

DSIS persists configuration for:

- COM port and baud rate;
- auto-detection and auto-reconnect;
- theme and compact sidebar;
- scan cooldown and minimum confidence;
- logging;
- automatic backup interval;
- attendance schedule;
- calendar exceptions;
- school/application name;
- first-run setup progress.

## Backup and restore

`data/attendance.db` is the live database.

Backups are timestamped snapshots under `data/backups/`.

Restore replaces the active database after permission and file/path validation. It is not a merge operation.

Before destructive operations such as device wipe or database restore, create a fresh backup.

## Security and privacy

DSIS uses local storage and does not require a cloud service for normal operation.

No encryption-at-rest claim is made. Deployers are responsible for securing the Windows host, database, settings, logs, and backup files and for meeting applicable institutional privacy requirements.

Do not place real student records, production databases, passwords, or sensitive logs into public commits.

## Reliability

Current reliability mechanisms include:

- device identity handshake before adopting a COM port;
- stale saved-port detection and fallback discovery;
- automatic reconnect;
- serial line buffering;
- JSON plus compatibility text parsing;
- operation-state cleanup after disconnect;
- database backups;
- structured logging;
- backend permission checks.

## Historical generations

DSIS has multiple generations of UI code:

| Generation | Implementation | Status |
| --- | --- | --- |
| v1 | CustomTkinter | Archived |
| v2 | PySide6 / Qt | Archived/reference |
| v3 | HTML/CSS/JavaScript + pywebview | Maintained |

Historical implementations are kept for regression comparison and project history. They are not the supported v3 launcher.

## Further documentation

- [v3 Workflows](v3-workflows.md)
- [Installation Guide](installation-guide.md)
- [v3 System Architecture](../Architecture/v3-system.md)
- [Database Schema](../Architecture/database-schema.md)
- [Hardware Connections](../Hardware/hardware-connections.md)
- [Troubleshooting](../Troubleshooting/README.md)
- [Testing Results](testing-results.md)

Last reviewed: 2026-09-20.