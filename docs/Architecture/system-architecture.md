# System Architecture

## Overview

The Digital Student Identification System (DSIS) is a layered application that combines embedded firmware, a desktop GUI, serial communication, and a local database to support attendance tracking with fingerprint biometrics.

The design separates concerns so that each part can be maintained independently, and the recent Python refactor strengthens that separation further. Raw serial data is handled in the communication layer, converted into structured scan outcomes in the attendance processor, persisted through the database layer, and presented through the GUI without overloading the interface with core workflow logic.

- firmware handles fingerprint capture and matching on the ESP32
- Python manages serial communication, desktop operations, and database access
- SQLite stores student and attendance data locally
- the GUI presents operators with a clear workflow for enrollment, scanning, backup, and reporting

## Objectives

The architecture is intended to support:

- reliable fingerprint enrollment and scan workflows
- easy deployment on Windows workstations
- maintainable code organization
- persistent runtime settings
- backup and restore for data safety
- clear separation between UI, logic, and hardware communication

## Refactored Python architecture

The Python side is organized around a small set of focused responsibilities:

- [python/core/serial_handler.py](../../python/core/serial_handler.py) manages serial connections, reads, reconnect handling, and device-state awareness.
- [python/core/attendance.py](../../python/core/attendance.py) converts incoming ESP32 output into structured scan results and applies cooldown and confidence rules.
- [python/core/database.py](../../python/core/database.py) remains the persistence layer for students, attendance records, reporting helpers, and backup-related operations.
- [python/gui_qt/main_qt.py](../../python/gui_qt/main_qt.py) is the primary modern Qt entry point and UI orchestrator, delegating business logic to the core modules rather than embedding it directly in the interface.

This keeps the GUI thinner, improves testability, and makes it easier to evolve the system over time.

## Layered structure

| Layer | Purpose | Main files |
| --- | --- | --- |
| Firmware | Reads fingerprints and responds to serial commands | firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino |
| Communication | Opens the serial port and parses responses | python/core/serial_handler.py, python/core/commands.py |
| Application logic | Processes scan results and coordinates attendance behavior | python/core/attendance.py, python/core/utils.py |
| Data layer | Stores students, attendance records, and backup snapshots | python/core/database.py |
| Presentation | Displays the GUI and exposes actions to the operator | python/gui_qt/main_qt.py and related Qt GUI modules (legacy `python/gui/` remains available for compatibility) |
| Configuration | Stores defaults for serial settings and permissions | python/config.py, data/settings.json |

## Core components

### Firmware component

The ESP32 sketch implements the embedded fingerprint workflow. It accepts commands such as scan, stop, enroll, delete, wipe, and list. When a fingerprint is matched or enrolled, it emits structured text over serial so the Python application can interpret the result.

### Communication component

The serial layer opens the selected COM port, reads incoming lines from the device, and reports connection state. It also handles reconnect attempts after disconnections and exposes the current state to the GUI so the interface can update its status consistently.

### Application logic component

The application logic translates raw fingerprint events into attendance entries, validates them, and coordinates interactions with the database. It also applies role-based permission checks before sensitive actions are allowed.

### Data layer component

The database layer is responsible for:

- storing student enrollment records
- writing attendance events
- supporting backup and restore operations
- providing helpful queries for reports and dashboards

### Presentation component

The GUI is organized into specific pages for attendance, student management, statistics, logs, and settings. This separation keeps the main window controller focused on workflow orchestration rather than every UI detail.

## Runtime workflow

1. The operator launches the app and clicks Connect.
2. The serial handler opens the selected COM port and begins reading device output.
3. The GUI sends commands for enrollment or scanning.
4. The firmware reports progress and results over serial.
5. The Python application updates the UI, stores records, and logs actions.
6. If the connection drops, reconnect logic attempts to restore it automatically.

## Enrollment flow

1. The operator starts Enrollment from the GUI.
2. The GUI sends an enrollment command to the ESP32.
3. The firmware captures the new fingerprint template.
4. The Python application stores the student profile in the SQLite database.

## Attendance flow

1. The operator starts scan mode.
2. The firmware compares the presented fingerprint to stored templates.
3. The Python application receives the result and writes an attendance event.
4. The GUI refreshes the attendance list and statistics.

## Settings and configuration

The application saves persistent preferences for:

- COM port selection
- baud rate
- theme mode
- cooldown behavior
- auto-reconnect behavior

These preferences are loaded from a JSON settings file so the app can remember operator choices between sessions.

## Reliability features

The design includes several safeguards:

- reconnect logic for temporary serial failures
- cooldown handling to reduce duplicate attendance logs
- permissions for destructive or privileged actions
- backup creation before restore workflows
- operation logs for troubleshooting and auditing

## Extension points

The architecture is structured so future work can be added without rewriting the entire system. Possible additions include:

- cloud sync
- RFID or face-recognition support
- richer audit trails
- export formats beyond Excel
- remote administration or mobile monitoring
