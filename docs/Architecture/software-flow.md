# Software Flow

## Overview

This document explains the runtime behavior of the application from startup through enrollment, scanning, logging, backup, and restore.

The current Python implementation uses a more structured flow than earlier versions: raw serial data is read and interpreted by the communication layer, transformed into attendance outcomes by the attendance processor, and then persisted and reflected in the UI.

## Startup flow

1. The user launches the application.
2. The Python app initializes configuration and logging.
3. The database is created or validated.
4. The GUI opens and the connection controls become available.

## Connection lifecycle

1. The user clicks Connect.
2. The serial handler opens the selected COM port.
3. A background reader loop begins consuming incoming serial lines.
4. The GUI updates connection status and enables actions as the device becomes available.
5. If the connection is lost, reconnect logic begins retrying automatically.

## Enrollment flow

1. The user chooses Enrollment from the GUI.
2. The GUI sends an enrollment command to the ESP32.
3. The firmware captures the fingerprint template.
4. The Python app waits for a successful response.
5. The student profile is written to the SQLite database.

## Attendance scanning flow

1. Scan mode is started from the GUI.
2. The ESP32 waits for a fingerprint.
3. When a fingerprint is presented, the device attempts matching.
4. The serial handler receives the raw output and passes it to the attendance processor.
5. The attendance processor interprets the scan result, applies cooldown and confidence rules, and returns a structured outcome.
6. The database layer records the event and the GUI refreshes the attendance view.
7. Unknown or unregistered scans are stored as history entries rather than being dropped.

## Backup and restore flow

1. The operator selects Backup from the GUI.
2. The database is copied to a timestamped backup file.
3. The operator can later restore from the list of available backups.
4. The active database is replaced with the selected snapshot.
5. The UI is refreshed to reflect the restored state.

## Permission flow

The GUI checks the current role before enabling actions. Protected operations such as delete, wipe, restore, export, and backup are restricted when the role does not permit them.

## Logging flow

Operational events are written to both the console and log files under the data/logs directory. This makes it easier to review connection problems, backup results, and attendance processing issues.
