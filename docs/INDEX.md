# DSIS Documentation Index

Welcome to the **Digital Student Identification System (DSIS)** documentation hub.

DSIS is a Windows-based student identification and attendance platform built around an ESP32 controller, AS608 fingerprint sensor, Python backend, HTML/JavaScript interface, pywebview, and SQLite storage. This index separates operator documentation from architecture, hardware, development, research, and historical material.

## 🚀 Start here

| Goal | Recommended document |
| --- | --- |
| Understand DSIS quickly | [Project Documentation](README.md) |
| Install DSIS from scratch | [Installation Guide](UserGuide/installation-guide.md) |
| Learn normal operation | [v3 User Workflows](UserGuide/v3-workflows.md) |
| Set up the ESP32 + AS608 | [Hardware Connections](Hardware/hardware-connections.md) · [Wiring](Hardware/wiring.md) |
| Understand the v3 software | [v3 System Architecture](Architecture/v3-system.md) |
| Understand the database | [Database Schema](Architecture/database-schema.md) |
| Fix a device/application problem | [Current Troubleshooting](Troubleshooting/README.md) |
| Build a portable Windows release | [Portable Build](../PORTABLE_BUILD.md) |
| Contribute code or documentation | [Contributing](../CONTRIBUTING.md) |

## 🧭 Documentation categories

### Architecture

Technical documentation describing how DSIS works internally.

- [Architecture Overview](Architecture/architecture.md)
- [System Architecture](Architecture/system-architecture.md)
- [v3 System Architecture](Architecture/v3-system.md)
- [Software Flow](Architecture/software-flow.md)
- [Database Schema](Architecture/database-schema.md)

### Hardware & firmware

Physical connections, firmware variants, serial communication, and device setup.

- [Hardware Connections](Hardware/hardware-connections.md)
- [Wiring](Hardware/wiring.md)
- [Firmware Variants](Hardware/firmware-variants.md)

### User & operator guides

Documentation for installing and operating the maintained v3 application.

- [Project Overview](UserGuide/project-overview.md)
- [Installation Guide](UserGuide/installation-guide.md)
- [v3 User Workflows](UserGuide/v3-workflows.md)
- [Testing Results](UserGuide/testing-results.md)
- [Current Troubleshooting](Troubleshooting/README.md)

### Development

Documentation for contributors and maintainers.

- [Documentation Map](Development/documentation-map.md)
- [Documentation Inventory](Documentation-Inventory.md)
- [Source/File Overview](Development/FILES_OVERVIEW.md)
- [Development Changelog](Development/change-log.md)
- [Database Updates](Development/database-updates.md)
- [Logging Guide](Development/logging-guide.md)
- [Runtime Data](Development/runtime-data.md)
- [Portable Python](Development/PORTABLE_PYTHON.md)
- [Tools Catalog](Development/tools-catalog.md)
- [UI Prototypes](Development/ui-prototypes.md)
- [Development TODO](Development/todo.md)

### Security

- [Security Audit Report](SECURITY_AUDIT_REPORT.md)
- [Security Remediation Status](SECURITY_REMEDIATION_REPORT.md)
- [Security Policy](../SECURITY.md)

### Project history & research

- [UI Lineage](History/ui-lineage.md)
- [Research](Research/)
- [DSIS Concept Paper](Research/DSIS_CONCEPT_PAPER.md)
- [Concept Paper Source Notes](Research/DSIS_CONCEPT_PAPER_SOURCE_NOTES.md)

### Generated and preserved material

- [Generated Documentation](generated/INDEX.md)
- [Duplicate / Superseded Documentation](Dup/README.md)
- [Archive](../archive/README.md)

These areas may contain point-in-time audits, experiments, duplicates, or historical implementations. Always check whether a document is marked current before using it as an implementation reference.

## 🔌 Current v3 runtime at a glance

```text
Windows Desktop
      │
      ▼
run_web_gui.py / run_web_gui.bat
      │
      ▼
pywebview + HTML/CSS/JavaScript
      │
      │ window.pywebview.api
      ▼
Python v3 API / Core Services
      │
      ├── SQLite database
      ├── Reports / CSV exports
      ├── Backups / restore
      ├── Permissions / authentication
      └── Serial discovery / device control
                    │
             USB Serial 115200
                    │
                    ▼
                  ESP32
                    │
             UART 57600
                    │
                    ▼
             AS608 fingerprint sensor
```

The current supported launcher is the v3 HTML/pywebview application. Legacy UI implementations and isolated prototypes remain available for historical or comparison purposes but are not the supported production launcher.

## 📌 Documentation rules

- Prefer current v3 documentation over legacy or generated material.
- When source behavior changes, update the corresponding documentation.
- Keep hardware pinouts, serial settings, permissions, database behavior, and user workflows synchronized with the implementation.
- Mark historical or experimental material clearly instead of presenting it as current behavior.
- Do not place real student records, passwords, fingerprint data, or other sensitive deployment data into public examples.

For the repository-wide documentation classification and source-of-truth rules, see [Documentation Map](Development/documentation-map.md) and [Documentation Inventory](Documentation-Inventory.md).

Last reviewed: 2026-09-20.
