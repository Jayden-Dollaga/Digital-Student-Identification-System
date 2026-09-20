# DSIS v3 Software Flow

This document describes the maintained DSIS v3 HTML/pywebview application from startup through device discovery, enrollment, attendance, reporting, backup, restore, and shutdown.

## 1. Startup

```text
run_web_gui.py / run_web_gui.bat
              |
              v
       gui_web.main_web
              |
              +--> configure exception hooks
              +--> create Api
              +--> initialize DB/settings/logging
              +--> start automatic-backup loop
              +--> create pywebview window
              |
              v
     python/gui_web/web/index.html
```

During `Api` initialization, DSIS loads saved settings, initializes SQLite, creates the serial handler and attendance processor, configures logging, restores attendance settings, and starts the automatic-backup due-check loop.

## 2. First-run setup

The setup order is **Password → Device → Schedule → Branding → normal application**.

The password is created during first-run setup. There is no built-in administrator fallback password. The active authentication implementation requires at least 8 characters and stores a salted PBKDF2-HMAC-SHA256 record using a random 16-byte salt and 310,000 iterations.

Device, schedule, and branding completion flags are persisted in `data/settings.json`, allowing an interrupted setup to resume.

## 3. Device discovery

```text
Connect
  |
  v
Enumerate Windows serial ports
  |
  v
Rank candidates using USB descriptors / VID:PID hints
  |
  v
Open candidate at 115200 baud
  |
  v
Send ID?
  |
  v
Validate DSIS identifier + protocol version
  |
  +---- failure --> try another candidate / report failure
  |
  +---- success -> adopt port + metadata
```

The discovery layer expects the identifier `Digital Student Identification System` and supports protocol version 1 or newer.

A saved COM port can become stale when an ESP32 is moved between USB ports or computers. The serial handler detects a missing saved port and can fall back to discovery.

## 4. Serial connection lifecycle

`SerialHandler` owns the live pyserial connection after discovery.

It handles port opening/closing, line buffering, command writes, device metadata, disconnect handling, stale-port recovery, and automatic reconnect attempts.

The PC-to-ESP32 connection uses **115200 baud**. The ESP32-to-AS608 UART uses **57600 baud** internally; 57600 is not the host COM-port setting.

After connection, the API requests the device fingerprint count.

## 5. Event flow

The firmware emits both human-readable compatibility messages and structured JSON. Examples:

```json
{"type":"status","state":"SCAN_MODE"}
```

```json
{"type":"attendance","event":"match","id":1,"confidence":223}
```

The backend forwards higher-level events to JavaScript through `window.dsisEvent(event, payload)`. Current event families include connection/status, serial lines, scan results, enrollment progress, delete/wipe progress, fingerprint count, logs, and device-mode changes.

## 6. Enrollment

```text
Student LRN + name + grade + section
                  |
                  v
             field validation
                  |
                  v
           ENROLL / ENROLL:id
                  |
                  v
          capture finger #1
                  |
                  v
             remove finger
                  |
                  v
          capture finger #2
                  |
                  v
             createModel()
                  |
             +----+----+
             |         |
          mismatch    success
             |         |
          failure  storeModel(id)
                       |
                       v
                device success
                       |
                       v
                save student row
```

`ENROLL` chooses the next free fingerprint slot. `ENROLL:<id>` accepts a specific ID from 1-127.

The local student record is saved only after the device reports successful template storage. Cancellation or disconnect clears the pending operation and returns the device to command mode.

## 7. Attendance scanning

The firmware captures a finger, converts the image, searches the sensor database, and emits a match, unknown, or low-confidence event.

The firmware-level match floor is **50** confidence. The Python application has a separate configurable `min_confidence`, default **100**:

| Confidence | Application status |
| ---: | --- |
| >= 100 | `GOOD MATCH` |
| < 100 | `WEAK MATCH` |

A `WEAK MATCH` is currently still recorded by the attendance processor. The application threshold is therefore a classification rule, not a second rejection gate.

Duplicate protection is layered: the firmware has an approximately 2-second post-scan delay, while the Python processor uses a per-fingerprint cooldown whose default is 10 seconds.

Unknown scans use reserved `fingerprint_id = 0` and the `Unregistered` database row.

## 8. Attendance status and calendar

Attendance presentation uses configured schedule and date-specific calendar exceptions.

| Setting | Default |
| --- | --- |
| Time in | 08:00 |
| Time out | 17:00 |
| Early threshold | 15 minutes |
| Late threshold | 15 minutes |
| Absent threshold | 0 minutes |

Supported calendar exception types are `holiday`, `suspension`, and `half_day`. A half-day can define its own time-in/time-out values.

## 9. Attendance evaluation

Evaluation supports **Day**, **Monday-Sunday Week**, and **Calendar Month**.

For each student, DSIS counts distinct attendance dates in the selected period. The evaluation's observed-day denominator is based on dates with attendance activity in the selected range; completely empty calendar dates are not automatically treated as school days by this evaluation.

| Rate | Category |
| ---: | --- |
| 90-100% | Excellent |
| 75-89% | Good |
| 50-74% | Needs attention |
| < 50% | Low attendance |

Results can be sorted by presence, attendance rate, or name. CSV export is permission-gated.

## 10. Student deletion

The v3 deletion workflow is device-first: the API sends `DELETE:<id>`, waits for the device result, and removes the local profile only after successful hardware deletion. A failed hardware delete leaves the local profile intact.

## 11. Wipe

**WIPE is destructive.** The current v3 workflow sends `WIPE` to the ESP32, waits for device success, then clears linked local student/attendance data and refreshes the fingerprint count.

If local cleanup fails after successful device wipe, the API reports that partial state rather than claiming both phases completed.

Create a fresh database backup before using wipe.

## 12. Backup and restore

Backups are timestamped SQLite snapshots under `data/backups/`. Automatic backups are checked by a background loop using the saved interval; the default is 25 minutes.

Restore is permission-gated and replaces the active database after backup-path/file validation. Restore is not a merge operation.

## 13. Permissions and sessions

The effective role is held in memory by `core.permissions`. The `current_role` value persisted in `data/settings.json` is for UI continuity and is not the authorization source.

| Role | Permissions |
| --- | --- |
| Administrator | scan, enroll, delete, wipe, export, backup, restore, attendance evaluation, calendar management |
| Teacher | scan, export, backup, attendance evaluation |
| Guest | scan, attendance evaluation |

Authenticated non-guest sessions expire after 600 seconds of inactivity by default.

## 14. Settings and runtime data

`data/settings.json` stores local preferences such as COM port, baud rate, theme, compact sidebar, auto-detection, auto-reconnect, cooldown, minimum confidence, logging, backup interval, schedule, calendar exceptions, school name, and first-run progress.

Default runtime directories include:

```text
data/attendance.db
data/settings.json
data/backups/
data/logs/
data/charts/
data/exports/
```

## 15. Logging

When enabled, the logger writes console output and timestamped per-run files under `data/logs/`, using a name such as `fingerprint_attendance_YYYYMMDD_HHMMSS.log`. Old matching files are pruned according to the configured retention count, default 7.

## 16. Shutdown

Closing the pywebview window invokes the API disconnect path. Uncaught main-thread and worker-thread exceptions are routed through the application logger.

## Source references

- `python/gui_web/api.py`
- `python/gui_web/main_web.py`
- `python/core/device_discovery.py`
- `python/core/serial_handler.py`
- `python/core/attendance.py`
- `python/core/attendance_status.py`
- `python/core/attendance_calendar.py`
- `python/core/database.py`
- `python/core/auth.py`
- `python/core/permissions.py`
- `python/settings_store.py`
- `firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino`

Last reviewed: 2026-09-20.