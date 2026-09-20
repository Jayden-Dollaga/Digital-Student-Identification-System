# DSIS Documentation

Welcome to the **Digital Student Identification System (DSIS)** documentation.

This documentation set is organized around the actual v3 application, its hardware/firmware stack, operational workflows, development internals, and historical material. The goal is to make the repository understandable to someone who has never worked on DSIS before.

## Where to start

| You are... | Start here |
| --- | --- |
| **New to DSIS** | [Documentation Index](INDEX.md) |
| **Installing DSIS** | [Installation Guide](UserGuide/installation-guide.md) |
| **Using the application** | [v3 Workflows](UserGuide/v3-workflows.md) |
| **Setting up the ESP32/AS608** | [Hardware](Hardware/hardware-connections.md) and [Wiring](Hardware/wiring.md) |
| **Trying to understand the software** | [v3 System Architecture](Architecture/v3-system.md) |
| **Working on the database** | [Database Schema](Architecture/database-schema.md) |
| **Using the web/Python bridge** | [API Reference](API/README.md) |
| **Debugging a connection/problem** | [Current Troubleshooting](Troubleshooting/README.md) |
| **Developing or contributing** | [Documentation Map](Development/documentation-map.md) and [Contributing](../CONTRIBUTING.md) |
| **Packaging DSIS for Windows** | [Portable Build](../PORTABLE_BUILD.md) |
| **Reviewing project history** | [UI Lineage](History/ui-lineage.md) |

## Documentation map

```text
docs/
├── Architecture/       System design, data flow, database, v3 internals
├── Hardware/           ESP32, AS608, wiring, firmware and serial requirements
├── UserGuide/          Installation, workflows, testing and operator guidance
├── Troubleshooting/    Current recovery procedures and diagnostics
├── Development/        Implementation notes, source maps, logs and project tracking
├── History/            v1/v2/v3 evolution and legacy context
├── Research/           Research, concept and exploratory material
├── API/                API/interface documentation and future expansion
├── generated/          Generated audits and repository analysis
└── Dup/                Preserved duplicates and superseded documentation
```

## Documentation authority

For the maintained application, prefer documentation that describes the **current v3 implementation**. Historical, generated, prototype, and archived material is retained for traceability but should not be treated as the current runtime contract unless explicitly stated.

The [Documentation Map](Development/documentation-map.md) and [Documentation Inventory](Documentation-Inventory.md) explain which documents are current, historical, generated, or preserved for reference.

## Core documentation

### Architecture

- [v3 System Architecture](Architecture/v3-system.md) — runtime layers, component responsibilities, serial protocol, application flow, enrollment, attendance, permissions, and data behavior.
- [System Architecture](Architecture/system-architecture.md) — broader system design.
- [Software Flow](Architecture/software-flow.md) — software execution and data movement.
- [Database Schema](Architecture/database-schema.md) — SQLite structure and relationships.

### Hardware

- [Hardware Connections](Hardware/hardware-connections.md) — supported hardware relationships and connections.
- [Wiring](Hardware/wiring.md) — ESP32/AS608 wiring reference.
- [Firmware Variants](Hardware/firmware-variants.md) — maintained and historical firmware variants.

### User operations

- [Installation Guide](UserGuide/installation-guide.md) — Windows, Python, firmware, drivers, and hardware setup.
- [v3 Workflows](UserGuide/v3-workflows.md) — first-run setup, connection, enrollment, scanning, attendance evaluation, reports, backups, restore, roles, and settings.
- [Testing Results](UserGuide/testing-results.md) — documented validation and test observations.
- [Current Troubleshooting](Troubleshooting/README.md) — concise recovery and diagnostics.

### API

- [v3 API Reference](API/README.md) — public JavaScript-to-Python bridge methods, events, permissions, and workflow contracts.

### Development and maintenance

- [Documentation Map](Development/documentation-map.md)
- [Source/File Overview](Development/FILES_OVERVIEW.md)
- [Logging Guide](Development/logging-guide.md)
- [Database Updates](Development/database-updates.md)
- [Runtime Data](Development/runtime-data.md)
- [UI Prototypes](Development/ui-prototypes.md)
- [Tools Catalog](Development/tools-catalog.md)
- [Development Changelog](Development/change-log.md)

## Research boundary

The `Research/` directory contains concept and study material. It is intentionally outside the operational product-documentation path and does not define current application behavior.

## Important distinction: current vs. historical

DSIS has gone through multiple UI and implementation generations. The current supported desktop application is the **v3 HTML/pywebview application** launched with `run_web_gui.py` or `run_web_gui.bat`.

Older Qt/CustomTkinter implementations and experimental prototypes remain in the repository because they are useful for comparison, regression investigation, and project history. They are not automatically supported production launchers.

## Documentation maintenance

When application behavior changes, update the documentation that describes that behavior in the same change whenever practical. In particular, keep the following synchronized with the source:

- Runtime architecture
- User workflows
- Hardware wiring and firmware behavior
- Database behavior
- Permissions and security behavior
- Installation and packaging instructions
- Troubleshooting procedures

For contribution and release requirements, see [CONTRIBUTING.md](../CONTRIBUTING.md) and [RELEASE.md](../RELEASE.md).

Last reviewed: 2026-09-20.
