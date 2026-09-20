# DSIS v3 User Workflows

This is the operator guide for the maintained DSIS v3 HTML/pywebview application.

## Launch

From the repository root:

```text
run_web_gui.bat
```

or:

```powershell
python run_web_gui.py
```

The supported v3 interface is a native pywebview window. Arduino IDE is needed for firmware work, not for ordinary daily operation.

## 1. First-run setup

The first-run wizard must complete before normal Dashboard use.

### Step 1 — Password

Create the initial administrator password.

- Minimum length: 8 characters
- Confirmation must match
- There is no built-in default administrator password
- Passwords are stored using PBKDF2-HMAC-SHA256
- Current implementation: random 16-byte salt and 310,000 iterations

### Step 2 — Device

Connect the ESP32 or choose to continue and connect it later.

DSIS can auto-detect the board or use a manual COM port. A device is accepted only after the firmware responds to `ID?` with valid DSIS identity metadata.

### Step 3 — Schedule

| Setting | Default |
| --- | --- |
| Time in | 08:00 |
| Time out | 17:00 |
| Early threshold | 15 minutes |
| Late threshold | 15 minutes |
| Absent threshold | 0 minutes |

### Step 4 — Branding

Set the school/application name and theme.

Device, schedule, and branding completion flags persist so an interrupted setup can resume.

## 2. Connect the ESP32

1. Connect the ESP32 with a data-capable USB cable.
2. Close Arduino Serial Monitor and other serial-terminal applications.
3. Start DSIS.
4. Leave auto-detection enabled unless a manual port is required.
5. Click **Connect**.
6. Confirm device metadata and fingerprint count.

The host-to-ESP32 connection uses **115200 baud**. The internal ESP32-to-AS608 UART uses **57600 baud** and is configured by the firmware.

### Stale COM port

Windows may assign a different COM number after the board is moved. Use **Forget saved port** and reconnect with auto-detection.

## 3. Enroll a student

Use the Students workflow with the `enroll` permission.

Required profile fields:

- Student LRN
- Full name
- Grade
- Section

### Enrollment sequence

1. Start enrollment.
2. Place the finger on the AS608.
3. Remove the finger.
4. Place the same finger again.
5. The ESP32 creates the fingerprint model.
6. The ESP32 stores the model in an ID from 1-127.
7. DSIS receives device success.
8. DSIS saves the student profile.

`ENROLL` chooses the next available ID; `ENROLL:<id>` requests a specific ID from 1-127.

The local student profile is saved only after the device confirms successful fingerprint storage.

## 4. Scan attendance

1. Confirm the ESP32 is connected.
2. Start **SCAN**.
3. Place a registered finger on the AS608.
4. Review student information, confidence, and attendance status.
5. Press **STOP** before enrollment, deletion, or wipe.

### Confidence behavior

The firmware emits a hardware match when AS608 confidence is at least **50**.

The Python attendance processor applies a separate configurable `min_confidence`, default **100**, to label the scan:

| Confidence | Application status | Recorded? |
| ---: | --- | --- |
| >= 100 | `GOOD MATCH` | Yes |
| 50-99 | `WEAK MATCH` | Yes |
| < 50 | No hardware match event | No |

A `WEAK MATCH` is still recorded by the current processor. The application threshold classifies the match; it does not reject it.

### Duplicate protection

- firmware post-scan delay: approximately 2 seconds;
- application per-fingerprint cooldown: 10 seconds by default.

### Unknown fingerprint

Unknown scans are stored using the reserved row:

```text
fingerprint_id = 0
student = Unregistered
```

## 5. Attendance status and calendar

Time-based attendance presentation uses the configured schedule.

Supported calendar exception types are `holiday`, `suspension`, and `half_day`.

A half-day can provide its own time-in/time-out values.

Calendar management requires the `manage_calendar` permission and is therefore an Administrator workflow in the default role configuration.

## 6. Attendance Evaluation

The Dashboard supports:

| Window | Range |
| --- | --- |
| Day | Selected calendar date |
| Week | Monday through Sunday |
| Month | Selected calendar month |

For each student, DSIS calculates distinct days present, days absent within the evaluation denominator, attendance rate, and category.

Current category bands:

| Attendance rate | Category |
| ---: | --- |
| 90-100% | Excellent |
| 75-89% | Good |
| 50-74% | Needs attention |
| below 50% | Low attendance |

The observed-day denominator is based on dates with attendance activity in the selected range. Completely empty calendar dates are not automatically counted as school days by this evaluation.

Results can be sorted by presence, attendance rate, or name. Authorized roles can export the selected evaluation as CSV.

## 7. Student deletion

Deletion is device-first:

```text
DELETE request
    ↓
DELETE:<fingerprint_id>
    ↓
ESP32 confirmation
    ↓
local student profile removed
```

If device deletion fails, the local profile remains. If deletion succeeds, existing attendance rows are re-linked to the reserved ID 0 `Unregistered` row so historical attendance events are preserved without keeping the deleted student profile.

## 8. Device wipe

**WIPE is destructive. Back up first.**

The v3 workflow sends `WIPE`, waits for confirmed device success, clears linked local student/attendance data, and refreshes the fingerprint count and affected views.

If hardware wipe succeeds but local cleanup fails, the API reports the partial state instead of claiming both phases succeeded.

## 9. Reports and CSV export

Reports read the live SQLite database.

CSV output is sanitized against spreadsheet formula-triggering values before writing.

Attendance Evaluation export uses the currently selected day/week/month window.

Export actions require the `export` permission.

## 10. Backup and restore

Manual backups are timestamped SQLite snapshots under `data/backups/`.

The application also runs an automatic backup due-check loop. The default saved interval is 25 minutes.

Restore requires the `restore` permission and replaces the active database with the selected supported backup. It is not a merge operation.

Create a fresh backup before restoring.

## 11. Roles and permissions

The effective role is held in an in-memory session. The persisted `current_role` setting is not trusted for authorization.

| Role | Permissions |
| --- | --- |
| Administrator | scan, enroll, delete, wipe, export, backup, restore, attendance evaluation, calendar management |
| Teacher | scan, export, backup, attendance evaluation |
| Guest | scan, attendance evaluation |

Authenticated non-guest sessions expire after 600 seconds of inactivity by default.

## 12. Settings

Persisted settings include COM port, baud rate, auto-detection, auto-reconnect, theme, compact sidebar, minimum confidence, scan cooldown, logging, automatic backup interval, attendance schedule, calendar exceptions, school name, and first-run progress.

Administrator-protected settings are enforced by the backend permission layer rather than only by disabled UI controls.

**Restore Defaults** restores application preferences and does not bypass authentication.

## 13. Normal shutdown

Close DSIS normally. The v3 shell invokes the API disconnect path and releases the serial connection.

Close DSIS before flashing firmware or opening Arduino Serial Monitor.

## Daily sequence

```text
Start DSIS
  ↓
Connect ESP32
  ↓
Verify metadata + fingerprint count
  ↓
Enroll / maintain students
  ↓
SCAN
  ↓
Review Attendance
  ↓
Evaluation / Reports
  ↓
Backup
  ↓
STOP
  ↓
Close DSIS
```

See [v3 System Architecture](../Architecture/v3-system.md) for technical details and [Troubleshooting](../Troubleshooting/README.md) for recovery procedures.

Last reviewed: 2026-09-20.