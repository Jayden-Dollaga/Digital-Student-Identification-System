# Data and Settings Model

DSIS keeps its working state in the local `data/` folder. This is not a remote service; the app expects to own a writable local folder on the workstation where it runs.

## Runtime data layout

| Path | Purpose |
| --- | --- |
| `data/settings.json` | persisted app settings and wizard state |
| `data/attendance.db` | SQLite database |
| `data/backups/` | timestamped snapshot copies |
| `data/logs/` | application log files |
| `data/exports/` | CSV exports |
| `data/charts/` | generated chart artifacts |

## Important settings keys

The default config is defined in `python/settings_store.py` and includes:

- `com_port` and `baud_rate`
- `theme`
- `auto_reconnect` and `auto_detect_serial`
- `cooldown`, `min_confidence`
- `time_in`, `time_out`, `school_weekdays_off`
- `school_calendar`
- `setup_device_step_done`, `setup_schedule_step_done`, `setup_branding_step_done`
- `current_role`
- `auth`

## Auth and security model

- password verification is handled through `core.auth`
- the role used for authorization is in memory, not loaded from disk
- `settings.json` stores auth state but is not treated as the source of truth for active privileges
- only a full password login establishes a session role

## Lifecycle and sensitivity

These files are operator sensitive:

- `settings.json` may contain saved role and schedule state
- `attendance.db` contains student records and attendance history
- `backups/` may contain copies of live data
- `logs/` may contain device and app diagnostics

Guard access to the runtime folder the same way you would guard any local student-record archive.
