# DSIS v3 Runtime Contract

This document describes how the maintained application moves from process startup to a recorded attendance event.

## 1. Startup

`run_web_gui.py` is the supported script entry point. `python/gui_web/main_web.py` loads configuration and settings, initializes the shared database and logging facilities, creates the API object, and opens the local HTML application in pywebview. The frontend is loaded from `python/gui_web/web/index.html`; the application does not depend on a separately hosted HTTP server.

The API object owns the long-lived serial handler and attendance processor. It also starts the background work needed for device monitoring, automatic backups, and event delivery. The exact timing of background work is implementation detail; callers should use returned state and events rather than assuming a fixed startup order.

## 2. Bridge direction

Frontend JavaScript calls Python methods through `window.pywebview.api`. Methods return JSON-compatible dictionaries, lists, booleans, and scalar values. Error responses use an `ok` field and a user-safe `message`; permission failures may also include an HTTP-like `status` and `requires_password` flag.

Python-to-frontend updates are delivered through the pywebview event bridge and handled by the frontend event dispatcher (`window.dsisEvent`). Events such as device status, serial output, attendance results, enrollment progress, wipe progress, data changes, and backup state allow the UI to refresh without polling every operation.

The bridge is a local process boundary, not a security boundary. It is intentionally backed by Python permission checks; hiding a button in JavaScript is not sufficient authorization.

## 3. Device lifecycle

1. The discovery layer enumerates candidate serial ports.
2. The handler probes candidates and recognizes a valid DSIS identity/handshake, including a device that is still emitting boot output.
3. A successful connection is followed by an identity/status synchronization so the application knows the selected port and device metadata.
4. Attendance scanning is requested with `SCAN` only when no enrollment, delete, wipe, or other command-mode operation is active.
5. Disconnects update UI state and may trigger the configured auto-reconnect policy. A stale saved port can be forgotten; a COM port alone is not proof of a DSIS device.

## 4. Enrollment lifecycle

The operator selects or confirms a sensor ID and enters validated student metadata. Python requests command mode and sends an enrollment command. Firmware guides the two fingerprint captures and reports progress. The application records progress events in the enrollment UI. The student row is written to SQLite only after the workflow has enough information to associate the sensor ID with the metadata. Failed or discarded enrollment must not be presented as a durable student record.

Sensor templates and SQLite rows are separate stores. A database backup does not back up the sensor; a restored database must be reconciled with the physical device before attendance use.

## 5. Attendance lifecycle

In scan mode, firmware emits a match, unknown, or low-confidence event. `core.attendance.AttendanceProcessor` parses the event, resolves a matched fingerprint ID against SQLite, and applies application policy:

- A match at or above `min_confidence` is classified `GOOD MATCH`.
- A match below that threshold is classified `WEAK MATCH`; the threshold is application configuration and must not be confused with the firmware's sensor-level minimum.
- Unknown scans are represented by reserved fingerprint ID `0`, status `UNKNOWN`, and the `Unregistered` placeholder.
- A fingerprint ID already processed within the configured cooldown is returned as not logged, with a cooldown reason.
- Accepted outcomes are written with confidence, status, timestamp, date/time fields, and an explicit event type where the database contract requires it.

Calendar and schedule logic then determines presentation such as time-in, time-out, late, early, half-day, absent, holiday, or suspension status. Those classifications are not inferred from the sensor alone.

## 6. Persistence and preservation

SQLite is the authoritative local store for student metadata and attendance records. Database initialization performs schema creation and migrations, enables foreign-key behavior, removes invalid legacy non-positive rows, and ensures the reserved ID `0` placeholder exists. The attendance event type migration backfills the first scan for a fingerprint/date as `time_in` and later scans as `time_out`.

Deleting a student does not erase historical attendance by default. Retained rows are reassigned to the unregistered identity so the system does not display a deleted student's name against a historical event. A full wipe is a coordinated destructive action: firmware deletion and local cleanup must be treated as one workflow and must be permission-gated.

## 7. Authorization

The active role is held in an in-memory session. Guest, teacher, and administrator capabilities are defined by `core.permissions`. Administrator elevation requires the password stored by `core.auth`; there is no built-in default password. Backend methods enforce permissions for student mutation, wipe, restore, export, backups, settings, time rules, and evaluation even if a frontend control is called directly.

## 8. Backup, restore, and export

Automatic and manual backups copy the SQLite database into the configured backup area. Restore is an administrator-level data operation and emits a data-change event so the UI can refresh. Exports read current local records and write a user-selected file; export permission is checked independently from viewing a report. Neither backups nor exports change the sensor templates.

## 9. What this contract does not promise

The contract does not promise network synchronization, cloud storage, biometric template backup, simultaneous multi-device operation, or a packaged v3 release unless those capabilities are present in the current source and release artifacts. Prototype and reference UI documents must not be used as evidence for those features.
