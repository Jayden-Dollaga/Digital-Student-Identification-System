# DSIS v3 API Reference

This reference documents the public Python bridge exposed to the active web UI as `window.pywebview.api`.

## API boundary

```text
JavaScript frontend
      |
      | window.pywebview.api
      v
python/gui_web/api.py
      |
      +--> core.serial_handler
      +--> core.database
      +--> core.attendance
      +--> core.auth / core.permissions
      +--> core.attendance_calendar
      +--> settings_store
```

The web frontend should use the bridge rather than accessing SQLite, pyserial, or filesystem internals directly.

## Connection and device operations

| Method | Purpose |
| --- | --- |
| `list_ports()` | List currently enumerated serial ports |
| `list_ports_detailed()` | Return COM ports with VID/PID and descriptions |
| `forget_saved_port()` | Clear the persisted preferred COM port |
| `connect(port="", baud=0, auto_detect=None)` | Connect to a DSIS device and request metadata/count |
| `disconnect()` | Close the device connection |
| `get_connection_status()` | Return current connection/device state |
| `start_scan()` | Enter fingerprint scan mode |
| `stop_scan()` | Leave scan mode |
| `request_fingerprint_count()` | Ask the ESP32 for stored template count |
| `reset_device()` | Reset the connected device |
| `send_serial_command(cmd)` | Send a validated serial command through the bridge |
| `get_serial_troubleshooting()` | Return connection troubleshooting information |
| `open_device_manager()` | Open the Windows device-management helper |
| `open_driver_help()` | Open driver/help workflow |

### Connection contract

The host connection uses 115200 baud by default. A successful connection requires the DSIS identity handshake; simply opening a COM port is not sufficient.

## Enrollment and fingerprint operations

| Method | Purpose |
| --- | --- |
| `start_enroll()` | Start a device enrollment operation |
| `cancel_enroll()` | Cancel the active enrollment |
| `discard_enrollment(fingerprint_id)` | Discard an enrollment/template when supported by the active workflow |
| `delete_on_device(fingerprint_id)` | Request hardware fingerprint deletion |
| `wipe_all_on_device()` | Request device-wide fingerprint wipe |
| `wipe_all_data()` | Execute the coordinated local-data wipe workflow |
| `validate_student_fields(student_no, student_name, grade, section)` | Return field validation feedback |

Enrollment is device-first. The local student profile is saved after successful device enrollment.

Wipe is destructive: the coordinated v3 workflow confirms the hardware wipe before clearing linked local student/attendance data.

## Student records

| Method | Purpose |
| --- | --- |
| `get_students()` | Return student records for the UI |
| `get_student(fingerprint_id)` | Return one student profile |
| `save_student(fingerprint_id, student_no, student_name, grade, section, previous_fingerprint_id=0)` | Create/update a profile |
| `delete_student(fingerprint_id)` | Delete a profile using the device-first workflow |
| `export_students_csv()` | Export student records |

The user-facing identifier is Student LRN; the database field remains `student_no` for compatibility.

## Attendance and reporting

| Method | Purpose |
| --- | --- |
| `get_dashboard_stats()` | Dashboard summary values |
| `get_recent_activity(limit=25)` | Recent attendance activity |
| `get_attendance(mode="today", offset=0)` | Attendance rows for the selected built-in view |
| `export_attendance_csv(mode="today", offset=0, week_start="")` | Export attendance rows |
| `get_attendance_evaluation(period="month", ref_date="")` | Day/week/month per-student evaluation |
| `export_attendance_evaluation_csv(period="month", ref_date="")` | Export the selected evaluation |
| `get_statistics_report()` | Statistics/report data |
| `export_statistics_report()` | Export statistics report |

Attendance Evaluation uses distinct attendance dates per student. The current UI category bands are 90-100% Excellent, 75-89% Good, 50-74% Needs attention, and below 50% Low attendance.

## Calendar

| Method | Purpose |
| --- | --- |
| `get_calendar_month(year, month)` | Load schedule exceptions for a month |
| `set_calendar_entry(date, entry_type, label="", time_in="", time_out="")` | Add/update a holiday, suspension, or half-day entry |
| `remove_calendar_entry(date)` | Remove a calendar exception |

Calendar management requires the `manage_calendar` permission.

## Backups

| Method | Purpose |
| --- | --- |
| `list_backups()` | List available database snapshots |
| `create_backup()` | Create a timestamped backup |
| `restore_backup(backup_path)` | Replace the active database from an authorized backup |

Restore is permission-gated and is a replacement, not a merge.

## Settings

| Method | Purpose |
| --- | --- |
| `get_settings()` | Read persisted application settings |
| `save_ui_settings(settings)` | Save permitted UI/runtime settings |
| `restore_default_settings()` | Restore application defaults |
| `get_current_role()` | Read effective role |
| `set_current_role(role)` | Request a role change through the session model |
| `get_role_permissions(role)` | Return configured permissions for a role |

Privileged setting changes are checked by the backend, not only by disabled UI controls.

## Authentication and sessions

| Method | Purpose |
| --- | --- |
| `is_first_run_setup_required()` | Determine whether initial setup is incomplete |
| `complete_first_run_setup(password, confirm_password)` | Create the initial administrator password |
| `get_setup_wizard_step()` | Return the next required setup step |
| `complete_setup_device_step(connected=False)` | Record device step completion |
| `complete_setup_schedule_step(...)` | Save and complete schedule setup |
| `complete_setup_branding_step(school_name="", theme="dark")` | Save and complete branding |
| `authenticate_role(role, password)` | Authenticate into a permitted role |
| `get_session_state()` | Return effective role, permissions, and session state |
| `touch_session()` | Refresh authenticated session activity |
| `lock_session()` | Return the session to the locked/guest state |
| `change_admin_password(current_password, new_password)` | Change the administrator password |

Passwords are created on first run; there is no built-in fallback administrator password. The authentication backend uses PBKDF2-HMAC-SHA256 with a 16-byte random salt and 310,000 iterations.

Non-guest sessions expire after 600 seconds of inactivity by default.

## Logs

| Method | Purpose |
| --- | --- |
| `open_log_folder()` | Open the local log directory |
| `get_app_log(max_lines=500)` | Return recent log output to the UI |

## Live events

The Python API can push events into the frontend through `window.dsisEvent(event, payload)`.

Known event families include:

- `scan_result`
- `serial_line`
- `log_line`
- `enroll_progress`
- `delete_progress`
- `wipe_progress`
- `fingerprint_count`
- `connection_status`
- `connection_changed`
- `connection_troubleshooting`
- `serial_error`
- `data_changed`
- `mode_changed`

## Authorization model

Default permissions:

| Role | Permissions |
| --- | --- |
| Administrator | scan, enroll, delete, wipe, export, backup, restore, attendance evaluation, calendar management |
| Teacher | scan, export, backup, attendance evaluation |
| Guest | scan, attendance evaluation |

The effective role is maintained in memory by `core.permissions`. The `current_role` field in `data/settings.json` is display continuity, not an authorization source.

## Source of truth

Keep this document synchronized with `python/gui_web/api.py` and `python/config.py`. For hardware protocol details, see [Firmware Variants](../Hardware/firmware-variants.md). For application flow, see [v3 System Architecture](../Architecture/v3-system.md).

Last reviewed: 2026-09-20.