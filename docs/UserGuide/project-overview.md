# Project Overview

## Project name

Digital Student Identification System (DSIS)

## Status

Prototype with ESP32 firmware, a Python desktop interface, SQLite storage, backup/restore support, reporting, and local UI action gating.

## Purpose

This project was built to automate attendance tracking using fingerprint recognition. Instead of relying on manual sign-in sheets, it uses a biometric sensor connected to an ESP32 and a desktop application that records attendance events and manages student data.

The Python application has also been refactored to make the system easier to maintain and more resilient during real-world use. Core responsibilities are now divided more clearly among the database, serial, attendance, and GUI modules so each layer can evolve independently.

## Refactor highlights

The current implementation now emphasizes:

- modular Python services instead of tightly coupled UI logic
- safer serial reading and reconnect handling for temporary connection interruptions
- centralized attendance processing with cooldown and confidence-aware behavior
- better testability for scan parsing and attendance logging flows

## What the system does

The system supports the full attendance lifecycle:

1. enroll a student and link a fingerprint template to that student
2. connect the desktop application to the ESP32 over serial
3. place a finger on the sensor to verify identity
4. record attendance events with time and confidence data
5. review records, generate reports, and export data
6. maintain backup copies of the database

The Dashboard also provides Attendance Evaluation for a selected day, Monday-to-Sunday week, or calendar month. It counts distinct dates with attendance activity, calculates each student's attendance rate, groups results into four categories, and exports the evaluation as CSV. Reports are available only to roles with `export` or `backup` permission.

Unknown scans are shown as `Unregistered` and persisted through the reserved `fingerprint_id = 0` system row. Roles gate actions in the local UI; they are not user authentication, and a person with access to the settings file can change the stored role.

## Hardware

| Component | Role |
| --- | --- |
| ESP32 | Main controller and serial bridge |
| AS608 fingerprint sensor | Reads and verifies fingerprint templates |
| Breadboard and jumper wires | Connect the sensor to the ESP32 |
| USB cable | Power and serial communication |
| Windows PC | Runs the Python application and database |

## Software stack

- Python 3.10 or newer (64-bit Windows recommended)
- HTML/CSS/JavaScript in a pywebview desktop window for the maintained v3 GUI
- PySide6/Qt and CustomTkinter as archived legacy interfaces only
- PySerial for serial communication
- SQLite for local persistence
- Matplotlib for charts
- OpenPyXL for Excel export
- Pillow for supporting image-related helpers and the legacy GUI
- Arduino IDE for firmware development

## Repository structure

```text
Digital Student Identification System (DSIS)/
├── firmware/                  # ESP32 sketches
├── python/                    # Python backend and GUI
├── data/                      # SQLite database, logs, exports, backups
├── docs/                      # Documentation
├── tests/                     # Validation and regression tests
├── requirements.txt           # Python dependencies
└── README.md                  # Main project entry point
```

## Core architecture

The application is split into clear layers:

- firmware layer: the sketch running on the ESP32
- communication layer: serial commands and responses
- application layer: Python logic for handling attendance and student operations
- presentation layer: the desktop GUI with separate page modules
- persistence layer: SQLite database and backup files

## Main workflow

### Enrollment flow

1. The user opens the GUI and connects to the ESP32.
2. The user starts enrollment mode.
3. The ESP32 captures a fingerprint template.
4. The Python app saves the student profile and links it to the fingerprint ID.

### Attendance flow

1. The user starts scanning mode.
2. A finger is placed on the sensor.
3. The ESP32 compares the input fingerprint to stored templates.
4. If matched, the Python app logs the attendance event.
5. The attendance list and reports update automatically.

## GUI modules

The active GUI is organized as a webview shell and a Python API bridge. The former page-based desktop modules remain in the archive for reference:

- `python/gui_web/main_web.py`: v3 webview launcher and window lifecycle
- `python/gui_web/api.py`: bridge from the web UI to the existing Python backend
- `python/gui_web/web/`: active HTML, CSS, and JavaScript interface
- `archive/legacy-ui/`: historical Qt and CustomTkinter page implementations

## Data handling

The application stores:

- student details
- fingerprint IDs
- attendance events
- timestamps and confidence scores
- backup snapshots

The SQLite database lives in the data directory and is used as the system’s primary persistent store.

## Configuration

Key settings are centralized in [python/config.py](../../python/config.py), including:

- serial port detection
- baud rate
- cooldown behavior
- role definitions
- backup and logging options

## Reliability features

The current system includes:

- serial reconnect handling
- local role-based action gating in the GUI (not authenticated authorization)
- backup creation and restore support
- log output for troubleshooting and operational visibility
- automatic attendance logging with cooldown protection
- persistent settings stored locally so COM port, baud rate, theme, cooldown, and auto-reconnect preferences are restored automatically
- light and dark web themes can be selected from Settings and are persisted with the other UI preferences
- type hints on core database and serial communication helpers to improve maintainability and IDE feedback

## Getting started

1. Install the Python dependencies with [install_requirements.bat](../../install_requirements.bat) or pip.
2. Upload the firmware to the ESP32.
3. Connect the hardware.
4. Launch the active v3 webview interface with [run_web_gui.bat](../../run_web_gui.bat) or `python run_web_gui.py`.
   - The Qt and CustomTkinter interfaces are retained only as archived historical snapshots under `archive/legacy-ui/`.
5. Enroll students and begin scanning.

> The GUI now opens larger by default so more of the user interface is visible on start.
>
> Automatic screen scaling is disabled in favor of a fixed layout for more predictable behavior on lower-spec and varied displays.

## Notes for future development

This project is a strong base for further expansion, including:

- cloud sync
- web-based dashboards
- multi-device support
- RFID or card-based fallback
- improved reporting and analytics

## Maintenance note

The project is intended to stay easy to maintain as it grows. Future work should focus on stronger testing, cleaner error handling, more reliable backup workflows, and better user-facing reporting.
