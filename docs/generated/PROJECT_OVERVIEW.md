# Project Overview

## Purpose

Digital Student Identification System (DSIS) is a hybrid hardware/software platform for biometric attendance tracking. It couples an ESP32-based fingerprint sensor controller with a Python desktop application, a local SQLite database, and user-facing GUI tools for enrollment, attendance logging, reporting, and device management.

## Why it exists

The project aims to provide a low-cost, deployable attendance system for classrooms, training centers, or small offices. By combining sensor-side fingerprint matching with a desktop application, it avoids the need for cloud infrastructure and supports offline operation, local data storage, and exportable reports.

## High-level architecture

- **Firmware layer**: ESP32 Arduino firmware that interfaces with the AS608 fingerprint sensor, controls a status LED, parses host commands, and streams attendance events over serial.
- **Core Python services**: serial communication, database persistence, attendance processing, firmware discovery, and logging.
- **Desktop UI**: two GUI stacks are present: legacy CustomTkinter for the original interface, and a more modern Qt-based interface for newer deployments.
- **Database**: SQLite used for student records, attendance logs, backups, exports, and reports.
- **Protocols**: Serial communication consists of a legacy plain-text protocol and a newer JSON-based protocol for device discovery, status, scan events, and host synchronization.

## Primary users

- **Administrators**: enroll students, manage database, export attendance, perform backups.
- **Teachers**: scan attendance and review reports.
- **Guests**: scan attendance only.

## Core workflows

- **Enrollment**: add a fingerprint template to the sensor and link it to a student profile in the database.
- **Scanning**: switch the ESP32 to scan mode, match fingerprint scans against stored templates, and record attendance events.
- **Student management**: create, edit, and delete student profiles with fingerprint IDs.
- **Reporting**: generate attendance summaries, statistics, and charts from stored records.
- **Firmware upload**: discover firmware files and flash the ESP32 using `esptool`.

## Notable implementation details

- The firmware emits both legacy text responses and JSON payloads for compatibility.
- The Python app centralizes serial parsing and attendance cooldown logic in `AttendanceProcessor`.
- Serial discovery uses port scoring and a JSON handshake command to identify the target ESP32.
- The system supports role-based permission sets defined in `config.py`.

## Existing documentation

- `README.md` provides install and quick-start guidance.
- `docs/Architecture/architecture.md` and related architecture docs describe the system at a high level.
- `docs/Development/*` holds implementation notes, migration summaries, and developer guidance.
