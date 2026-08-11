# Digital Student Identification System (DSIS)

This project begin as a practical hardware experiment: connect a fingerprint sensor to an ESP32, read biometric input, and use a desktop application to manage attendance records. It has since grown into a complete attendance-management platform with linked firmware, a Python application, a local database, and reporting tools.

The Python layer has recently been refactored around clearer responsibilities so database access, serial communication, attendance processing, and the GUI are easier to maintain, test, and extend without changing the overall user workflow.

## Refactor highlights

Recent improvements in the Python codebase include:

- clearer separation of concerns between persistence, serial handling, attendance processing, and UI orchestration
- more reliable serial communication with safer reconnect behavior and better connection-state handling
- centralized attendance parsing and cooldown protection through `AttendanceProcessor`
- stronger regression coverage for scan-processing behavior and better maintainability for future enhancements

---

## Table of Contents

- [What this project does](#what-this-project-does)
- [Project goals](#project-goals)
- [How the system works from the start](#how-the-system-works-from-the-start)
- [Hardware used](#hardware-used)
- [Software stack](#software-stack)
- [Project structure](#project-structure)
- [Installation and setup](#installation-and-setup)
- [Typical workflow](#typical-workflow)
- [ESP32 command reference](#esp32-command-reference)
- [Roles and permissions](#roles-and-permissions)
- [Database and data handling](#database-and-data-handling)
- [Automation and reliability](#automation-and-reliability)
- [Development notes and project evolution](#development-notes-and-project-evolution)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Version notes](#version-notes)

---

## Quick Start

The fastest way to try the GUI on Windows:

1. Install dependencies (one-time):

```bash
install_requirements.bat
```

1. Launch the desktop GUI:

```bash
run_qt_gui.bat
```

If you need the older CustomTkinter UI for compatibility, use `run_app.bat` instead.

### Run it again

After the first setup, start the app again with the same command:

```bash
run_qt_gui.bat
```

### Qt UI (recommended for modern Windows setups)

The newer Qt-based interface has improved serial connect behavior, theme switching, and auto-discovery support.

```bash
run_qt_gui.bat
```

Or, if you prefer the command line:

```bash
python run_qt_gui.py
```

Command-line alternatives:

```bash
python -m pip install -r requirements.txt   # Optional
python python/gui/app.py                    # Run GUI directly
python python/main.py                       # Run console mode (serial CLI)
```

> Note: If Pillow fails to install on Python 3.14, use Python 3.13 for the legacy GUI or install the Qt UI with `python run_qt_gui.py` instead.

---

## What this project does

The system is designed for schools, offices, or training centers and supports:

- enroll students with fingerprint data
- scan fingerprints for attendance verification
- store attendance records with timestamps and confidence values
- manage student details in a local database
- view attendance analytics and reports
- back up and restore database snapshots
- restrict actions by user role
- communicate with a fingerprint sensor over serial using an ESP32

In short, it covers the full biometric attendance workflow from sensor input to data storage and reporting.

---

## Project goals

This project was designed to be:

- affordable and easy to build with common hardware
- modular so each layer can be maintained independently
- practical for real-world attendance use
- suitable for small to medium educational or organizational deployment
- extensible for future features such as cloud sync, RFID, or face recognition

---

## How the system works from the start

1. A student is enrolled through the GUI.
2. The Python application sends an enrollment command to the ESP32.
3. The ESP32 reads the fingerprint from the AS608 sensor and stores it internally.
4. The student profile is saved in the SQLite database.
5. Later, the user starts attendance mode.
6. The ESP32 waits for a fingerprint scan and identifies it if it matches a stored template.
7. The Python app logs the attendance event and saves it to the database.
8. The user can review logs, statistics, backups, and exports from the desktop interface.

This is the full lifecycle of the system, from hardware registration to attendance reporting.

---

## Hardware used

| Component | Purpose |
| --- | --- |
| ESP32 DevKit / WROOM-32 | Main controller and serial bridge |
| AS608 fingerprint sensor | Captures and matches fingerprints |
| USB cable | Connects the ESP32 to the computer |
| Breadboard and jumper wires | Wiring between the sensor and ESP32 |
| Windows PC | Runs the Python GUI and database logic |

### Typical wiring

| AS608 wire | Color | ESP32 connection |
| --- | --- | --- |
| V+ | Purple | 3.3V |
| GND | Blue | GND |
| TX | Orange | RX pin |
| RX | White | TX pin |

The exact GPIO mapping may vary depending on the firmware and hardware layout. The current firmware expects a serial-based connection between the ESP32 and the sensor module.

---

## Software stack

- Python 3.13+
- CustomTkinter for the desktop GUI
- PySerial for serial communication
- SQLite for local data storage
- Matplotlib for charts and reports
- OpenPyXL for Excel export
- Pillow for image-related helpers
- Arduino IDE for compiling and uploading firmware

---

## Project structure

```text
Fingerprint-Attendance-System/
├── archive/                      # Experimental, diagnostic, and legacy UI artifacts preserved for reference
├── firmware/                     # ESP32 Arduino sketches and firmware sources
│   ├── attendance/
│   ├── enroll/
│   ├── delete/
│   ├── test/
│   └── ESP32_Fingerprint_AllInOne/
├── python/
│   ├── main.py                   # Console/legacy entry point for serial + CLI flow
│   ├── config.py                 # Environment-aware runtime configuration
│   ├── core/                     # Core services: DB, serial, attendance, logging, firmware helper
│   ├── gui/                      # Original CustomTkinter desktop UI
│   ├── gui_qt/                   # Modern PySide6 desktop UI and worker integration
│   ├── services/                 # Backup and export helpers
│   └── settings_store.py         # JSON-based settings persistence for GUI preferences
├── data/                         # Local database, backups, logs, exports, runtime state
├── docs/                         # Documentation and status notes
├── tests/                        # Regression tests and GUI coverage
├── tools/                        # Portable build, bootstrap, and packaging helpers
├── requirements.txt              # Python dependencies
├── run_app.bat                   # Launcher for the legacy GUI
├── run_qt_gui.py                 # Launcher for the Qt-based GUI
└── LICENSE
```

### File-by-file purpose guide

- [python/main.py](python/main.py) — legacy application entry point for serial communication and the console-style workflow.
- [python/config.py](python/config.py) — central runtime configuration with environment overrides and portable path logic.

## Recent maintenance changes

The project includes several low-risk maintenance improvements to harden serial, database, and firmware upload behavior:

- Normalized VID:PID formatting to zero-padded 4-digit hex for consistent device discovery and UI labeling.
- Use the discovery-returned canonical serial port for opening connections to avoid casing/normalization mismatches.
- Increased SQLite connection timeout to 30s to reduce transient 'database is locked' errors under concurrent access.
- Improved firmware upload timeout handling: esptool subprocesses are killed on timeout and a clear error message is returned.
- Added `tests/test_vidpid_normalization.py` to protect VID:PID normalization and scoring.

These changes are low-risk and backwards-compatible; they improve reliability without changing public APIs.

- [python/core/attendance.py](python/core/attendance.py) — parses ESP32 serial output into attendance events and applies cooldown logic.
- [python/core/commands.py](python/core/commands.py) — wraps ESP32 commands like scan, stop, enroll, delete, wipe, and list.
- [python/core/database.py](python/core/database.py) — SQLite persistence layer for students, attendance, backups, exports, and reset operations.
- [python/core/firmware_helper.py](python/core/firmware_helper.py) — searches for firmware binaries and uploads them over serial using esptool.
- [python/core/logger.py](python/core/logger.py) — centralized logging with rotation and consistent message formatting.
- [python/core/serial_handler.py](python/core/serial_handler.py) — low-level serial port connection, read/write, and reconnect management.
- [python/core/utils.py](python/core/utils.py) — shared formatting and helper routines used across the app.
- [python/gui/app.py](python/gui/app.py) — original CustomTkinter main window and orchestration layer.
- [python/gui/attendance_page.py](python/gui/attendance_page.py) — attendance list view for the legacy desktop UI.
- [python/gui/dashboard.py](python/gui/dashboard.py) — dashboard widgets and summary UI for the legacy app.
- [python/gui/dialogs.py](python/gui/dialogs.py) — enrollment, wipe, restore, and other modal dialogs.
- [python/gui/settings_dialog.py](python/gui/settings_dialog.py) — settings popup with COM port and firmware helper controls.
- [python/gui/settings_page.py](python/gui/settings_page.py) — settings page for the legacy GUI shell.
- [python/gui/sidebar.py](python/gui/sidebar.py) — sidebar navigation for the legacy desktop UI.
- [python/gui/students_page.py](python/gui/students_page.py) — student roster and management UI.
- [python/gui_qt/main_qt.py](python/gui_qt/main_qt.py) — launcher for the newer PySide6 Qt interface.
- [python/gui_qt/main_window.py](python/gui_qt/main_window.py) — main Qt shell with sidebar, header, and page switching.
- [python/gui_qt/pages](python/gui_qt/pages) — page implementations for dashboard, attendance, students, logs, reports, and settings.
- [python/gui_qt/widgets](python/gui_qt/widgets) — reusable Qt widgets such as the sidebar and stat cards.
- [python/gui_qt/workers/serial_worker.py](python/gui_qt/workers/serial_worker.py) — background worker for serial communication and live scan parsing.
- [python/services/backup.py](python/services/backup.py) — backup and restore service for database snapshots.
- [python/services/excel_export.py](python/services/excel_export.py) — Excel export helpers for attendance and student data.
- [python/settings_store.py](python/settings_store.py) — JSON persistence layer for GUI settings.
- [run_qt_gui.py](run_qt_gui.py) — repo-root launcher for the Qt interface, so you can start it without changing directories.

---

## Installation and setup

### Portable Windows build

To build a portable Windows executable for field testing:

```bash
python -m pip install -r requirements.txt
tools\build_portable.bat
```

The build output will be created in the folder [dist/portable](dist/portable). The generated executable can be copied to a USB drive and launched on another Windows machine without needing a separate Python installation.

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Upload the firmware

Open the Arduino sketch in [firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino](firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino) and upload it to the ESP32 through the Arduino IDE.

For a line-by-line firmware explanation, see [docs/Development/ESP32_Fingerprint_AllInOne_firmware_explanation.md](docs/Development/ESP32_Fingerprint_AllInOne_firmware_explanation.md).

The firmware now uses the onboard ESP32 D2 LED as a simple status indicator:

- slow blink (1 second ON / 1 second OFF): system ready / idle
- double blink every 2 seconds: attendance scan mode active
- fast blink (200 ms ON / OFF): enrollment in progress
- solid ON for 2–3 seconds: fingerprint matched successfully or fingerprint stored
- rapid flashing (100 ms ON / OFF for 5 seconds): error or failed enrollment

### 3. Connect the hardware

Make sure the fingerprint sensor and ESP32 are wired correctly and that the serial connection is available.

### 4. Install dependencies (Windows)

Double-click [install_requirements.bat](install_requirements.bat) to install the Python dependencies.

### 5. Run the GUI application

Double-click [run_qt_gui.bat](run_qt_gui.bat) to launch the desktop GUI.

If you need the legacy CustomTkinter interface, use `run_app.bat` instead.

If you prefer the command line, you can also run:

```bash
python run_qt_gui.py
```

> The GUI now opens larger by default so more of the interface fits on the screen.
>
> Automatic screen scaling has been removed to keep the interface layout stable across different displays.

---

## Typical workflow

### Enrollment

1. Open the app and connect to the ESP32.
2. Select the enrollment action.
3. Place a finger on the sensor.
4. Confirm the process in the GUI.
5. Enter or review student information.
6. Save the student profile to the database.

### Attendance scanning

1. Start scanning mode.
2. Place a registered finger on the sensor.
3. The ESP32 attempts to match the fingerprint.
4. If matched, the attendance event is stored.
5. The attendance view updates and the record becomes visible in the database.

### Data review and export

- open the attendance list
- inspect student records
- export data to Excel
- view charts and analytics
- create backups and restore previous versions if needed

---

## ESP32 command reference

| Command | Purpose |
| --- | --- |
| SCAN | Start attendance scanning mode |
| STOP | Exit scanning mode |
| ENROLL | Enroll a new fingerprint using the next available slot |
| ENROLL:1 | Enroll a fingerprint as a specific ID |
| DELETE:1 | Delete a specific fingerprint |
| WIPE | Remove all stored fingerprints |
| LIST | Show stored fingerprint count |

### LED status guide

The onboard D2 LED on the ESP32 provides quick feedback while the device is running:

- Ready / idle: slow blink (1 second ON / OFF)
- Attendance scan mode: double blink every 2 seconds
- Enrollment in progress: fast blink (200 ms ON / OFF)
- Successful match or stored fingerprint: solid ON for 2–3 seconds
- Error state: rapid flashing (100 ms ON / OFF for 5 seconds)

---

## Roles and permissions

The application supports role-based access so different users can work with different levels of control.

| Role | Permissions |
| --- | --- |
| Administrator | Full access including scan, enroll, delete, wipe, export, backup, and restore |
| Teacher | Scan, export, and backup access |
| Guest | Scan-only access |

The current role can be changed from the GUI and the available actions update immediately.

---

## Database and data handling

The system uses SQLite to store:

- student details
- fingerprint IDs
- attendance events
- timestamps and confidence values
- backup metadata

The database is stored under [data/attendance.db](data/attendance.db), and backup snapshots are stored under [data/backups](data/backups).

### Backup behavior

- backups are created as timestamped database snapshots
- previous backups can be restored from the GUI
- backups help protect against accidental data loss

---

## Automation and reliability

The current system includes:

- automatic serial port detection when possible
- reconnect logic for dropped serial connections
- cooldown handling to avoid duplicate attendance logging
- logging for operational visibility
- permission checks in the GUI so restricted actions are disabled for lower-privileged roles
- persistent user settings stored in a JSON file for COM port, baud rate, theme, cooldown, and auto-reconnect behavior
- type hints added to key database and serial helper functions to improve readability and editor support

### Settings persistence

The app now saves user preferences to [data/settings.json](data/settings.json) so the interface remembers your choices between sessions.

Saved settings include:

- COM port
- baud rate
- attendance cooldown
- theme mode
- auto-reconnect preference

These values are loaded automatically when the app starts and can be updated from the Settings dialog.

---

## Development notes and project evolution

This project has evolved in stages:

1. Initial prototype for fingerprint enrollment and scanning
2. Addition of a desktop GUI for easier operation
3. Integration with SQLite for persistent storage
4. Addition of charts, export, backup, and restore features
5. Refactoring of the GUI into modular page-based components for maintainability

The current GUI structure is organized around page modules instead of one large monolithic window file, which makes the code easier to understand and extend.

---

## Troubleshooting

If the app does not connect to the ESP32:

- confirm the ESP32 is powered and connected
- close the Arduino Serial Monitor if it is holding the COM port
- check that the correct serial port is selected
- verify the baud rate matches the firmware
- confirm the firmware was uploaded successfully

If fingerprint enrollment or scanning behaves unexpectedly:

- verify the sensor wiring
- check whether the ESP32 is still in the expected mode
- inspect the application log output
- test the firmware separately if needed

---

## License

This project is provided for educational and institutional use. Please review the license file for details.

---

## Version notes

- Current focus: maintainability, reliability, and a cleaner user experience
- The GUI has been reorganized into modular page-based components
- Serial device detection has been improved to prefer likely USB UART ports over unrelated devices
