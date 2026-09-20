# DSIS v3 Project Overview

> **Document status:** Current v3 reference  
> **Audience:** Users, teachers, administrators, developers, reviewers, and maintainers

The **Digital Student Identification System (DSIS)** is a local-first student identification and attendance platform built around an **ESP32**, an **AS608 fingerprint sensor**, and a **Windows desktop application**.

DSIS is designed to replace repetitive manual attendance workflows with a controlled digital process: identify a student, record an attendance event, evaluate attendance over a selected period, and export or back up the resulting records.

## At a glance

| Area | Current implementation |
| --- | --- |
| Desktop platform | Windows |
| Application UI | HTML/CSS/JavaScript in pywebview |
| Backend | Python |
| Database | SQLite |
| Device controller | ESP32 WROOM-32 |
| Fingerprint sensor | AS608 |
| PC ↔ ESP32 | USB serial, 115200 baud |
| ESP32 ↔ AS608 | UART, 57600 baud |
| Identification | Fingerprint template matching |
| Reports | Attendance history, evaluation, CSV export |
| Backup | Local database snapshots |
| Authentication | Administrator password + role session |
| Configuration | Local JSON settings |

## What DSIS does

The maintained v3 application covers the following lifecycle:

```text
Configure system
      │
      ▼
Connect ESP32
      │
      ▼
Enroll student ────────► Fingerprint template stored on sensor
      │
      ▼
Scan fingerprint
      │
      ├── Match ───────► Student resolved ───────► Attendance saved
      │
      └── Unknown ─────► Unregistered event
                                      │
                                      ▼
                              Reports / Evaluation
                                      │
                                      ▼
                                CSV / Backup
```

## Core capabilities

### Student records

- Student LRN is the user-facing identifier.
- The database retains `student_no` for compatibility.
- Student name, grade, section, fingerprint ID, and related profile information are stored locally.
- A fingerprint ID is assigned by the ESP32 during successful enrollment.
- A student record is not finalized until the device reports successful enrollment.

### Identification and attendance

- Fingerprint scans are processed by the ESP32 and reported to the desktop application.
- Matching events include fingerprint identity and confidence information where supplied by the device.
- A configurable minimum confidence threshold can reject weak matches.
- Attendance cooldown logic prevents rapid duplicate events from becoming multiple attendance records.
- Unknown scans use the reserved `fingerprint_id = 0` / `Unregistered` system row.
- Attendance records contain explicit date/time information and event metadata.

### Attendance evaluation

The Dashboard provides evaluation for:

- a selected day;
- a Monday-to-Sunday week; or
- a calendar month.

The evaluation counts **distinct dates with observed attendance activity** in the selected window. It calculates days present, days absent, and attendance rate, then assigns the application's attendance category. Sorting can be performed by presence, rate, or name.

CSV export is separate from the live SQLite database and should be treated as an exported report, not a second source of truth.

## Roles and permissions

Roles are local application permissions combined with an authenticated administrator session. They should not be interpreted as a full school identity-management system.

| Role | Typical access |
| --- | --- |
| **Administrator** | Full supported workflow: device operations, enrollment, deletion, wipe, reports, export, backup/restore, settings, and maintenance |
| **Teacher** | Scanning, reporting/export, backup, and attendance evaluation |
| **Guest** | Scanning and attendance evaluation |

Protected operations are checked by the Python bridge rather than relying only on hiding frontend buttons.

## Architecture

DSIS is separated into runtime layers so hardware, business logic, presentation, and persistence can evolve independently.

```text
┌───────────────────────────────────────────┐
│             Web UI / Browser Layer        │
│ HTML · CSS · JavaScript · app.js          │
└───────────────────┬───────────────────────┘
                    │ window.pywebview.api
┌───────────────────▼───────────────────────┐
│              Python API Bridge             │
│ python/gui_web/api.py                     │
└───────────────────┬───────────────────────┘
                    │
       ┌────────────┼──────────────┐
       ▼            ▼              ▼
   Attendance   Serial/device   Permissions
   processor      services        + auth
       │            │              │
       └────────────┼──────────────┘
                    ▼
             SQLite / backups
                    │
                    │ USB serial
                    ▼
                 ESP32
                    │ UART
                    ▼
              AS608 sensor
```

See the detailed [v3 System Architecture](../Architecture/v3-system.md) for component responsibilities, protocol behavior, synchronization rules, and lifecycle details.

## Hardware

| Component | Role | Important notes |
| --- | --- | --- |
| ESP32 WROOM-32 | Controller and serial bridge | Verified firmware target: ESP32 Dev Module |
| AS608 | Fingerprint acquisition/matching | Exact power requirements depend on module revision |
| USB cable | PC power + serial transport | Must support data, not charge-only |
| Breadboard/jumpers | Sensor wiring | Secure connections are important for reliable UART |
| Windows PC | Runs DSIS and stores local data | Hosts the Python/pywebview application |

### Maintained wiring

| AS608 | ESP32 |
| --- | --- |
| TX | GPIO14 / UART2 RX |
| RX | GPIO27 / UART2 TX |
| GND | GND |
| V+ | Sensor-revision-appropriate regulated supply |

TX/RX are intentionally crossed. See [Hardware Connections](../Hardware/hardware-connections.md) and [Wiring](../Hardware/wiring.md) before changing the physical setup.

## Software stack

- Python 3.10+; 64-bit Windows is recommended.
- pywebview for the native desktop window.
- HTML/CSS/JavaScript for the active interface.
- PySerial for device communication.
- SQLite for local persistence.
- Matplotlib for charts.
- OpenPyXL for spreadsheet export support.
- Pillow for image helpers and retained legacy functionality.
- Arduino IDE / Arduino CLI for firmware development and upload.

Qt/PySide6 and CustomTkinter are **historical interfaces** retained under `archive/legacy-ui/`. They are not the maintained v3 launcher.

## Data locations

The application uses the `data/` directory for runtime state such as:

- SQLite database;
- JSON settings;
- timestamped logs;
- database backups;
- generated exports and charts where applicable.

Do not commit real student information, passwords, fingerprint data, or deployment backups to the public repository.

See [Runtime Data](../Development/runtime-data.md) for retention and sensitivity guidance.

## Reliability behavior

The v3 application includes:

- automatic/manual serial discovery;
- DSIS identity handshake validation;
- serial reconnect handling;
- persistent operator settings;
- attendance cooldown processing;
- backup and restore workflows;
- device fingerprint-count refresh;
- operation-state cleanup after disconnects;
- structured logging;
- permission checks at the Python bridge;
- first-run administrator setup.

## First-run behavior

A new installation uses a setup router before normal operation. The setup flow establishes the administrator password and can guide device, schedule, and branding configuration.

The administrator password is hashed before being stored. The effective role is maintained as an in-memory session rather than being treated as a value that can simply be changed in the UI configuration file.

## Repository structure

```text
Digital-Student-Identification-System/
├── firmware/                 # Maintained ESP32 firmware
├── python/                   # Active Python backend and v3 web UI
├── data/                     # Runtime database, settings, logs, backups
├── docs/                     # User, architecture, hardware and developer docs
├── tests/                    # Automated and hardware validation
├── tools/                    # Diagnostics and maintenance tools
├── archive/                  # Historical implementations and diagnostics
├── Build/                    # Packaging specifications
├── run_web_gui.py            # v3 launcher
├── run_web_gui.bat           # Windows launcher
└── README.md                 # Repository entry point
```

## Recommended reading order

**New user:**

1. [Installation Guide](installation-guide.md)
2. [Hardware Connections](../Hardware/hardware-connections.md)
3. [v3 Workflows](v3-workflows.md)
4. [Troubleshooting](../Troubleshooting/README.md)

**Developer:**

1. [v3 System Architecture](../Architecture/v3-system.md)
2. [Database Schema](../Architecture/database-schema.md)
3. [Source/File Overview](../Development/FILES_OVERVIEW.md)
4. [Detailed Module Guide](../Development/FILES_DETAILED.md)
5. [Logging Guide](../Development/logging-guide.md)
6. [Contributing](../../CONTRIBUTING.md)

## Current limitations and future expansion

The current identification path is fingerprint-based. The architecture is intentionally modular so additional identification mechanisms can be evaluated later, including RFID/card-based workflows or multiple device support.

Potential future work should preserve the separation between device communication, attendance processing, persistence, permissions, and presentation instead of coupling new functionality directly to the web UI.

## Source of truth

When this document conflicts with the implementation, prefer:

1. current source code and tests;
2. current v3 architecture documentation;
3. current user/hardware guides;
4. historical or generated reports only for context.

Last reviewed: 2026-09-20.
