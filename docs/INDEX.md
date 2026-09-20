# DSIS Documentation Index

Welcome to the **Digital Student Identification System (DSIS)** documentation hub.

The current documentation describes the maintained v3 application, the ESP32/AS608 hardware stack, operational workflows, developer interfaces, data model, troubleshooting, and release/deployment process.

## Start here

| Goal | Document |
| --- | --- |
| Understand the project | [Project Overview](UserGuide/project-overview.md) |
| Install DSIS | [Installation Guide](UserGuide/installation-guide.md) |
| Operate the application | [v3 Workflows](UserGuide/v3-workflows.md) |
| Understand the architecture | [v3 System Architecture](Architecture/v3-system.md) |
| Understand data flow | [Software Flow](Architecture/software-flow.md) |
| Understand the database | [Database Schema](Architecture/database-schema.md) |
| Use the Python/web bridge | [API Reference](API/README.md) |
| Wire the hardware | [Wiring](Hardware/wiring.md) |
| Understand firmware | [Firmware Variants](Hardware/firmware-variants.md) |
| Recover from failures | [Troubleshooting](Troubleshooting/README.md) |
| Review validation | [Testing Results](UserGuide/testing-results.md) |

## Architecture

- [v3 System Architecture](Architecture/v3-system.md)
- [System Architecture](Architecture/system-architecture.md)
- [Software Flow](Architecture/software-flow.md)
- [Database Schema](Architecture/database-schema.md)

## Hardware

- [Hardware Connections](Hardware/hardware-connections.md)
- [Wiring](Hardware/wiring.md)
- [Firmware Variants](Hardware/firmware-variants.md)

## User and operator guides

- [Project Overview](UserGuide/project-overview.md)
- [Installation Guide](UserGuide/installation-guide.md)
- [v3 Workflows](UserGuide/v3-workflows.md)
- [Testing Results](UserGuide/testing-results.md)
- [Current Troubleshooting](Troubleshooting/README.md)
- [Long Troubleshooting Reference](TROUBLESHOOTING.md)

## Development

- [Documentation Map](Development/documentation-map.md)
- [Documentation Inventory](Documentation-Inventory.md)
- [Documentation Overhaul](Documentation-Overhaul.md)
- [Source Tree Overview](Development/FILES_OVERVIEW.md)
- [Detailed Python Module Guide](Development/FILES_DETAILED.md)
- [Database Maintenance](Development/database-updates.md)
- [Logging Guide](Development/logging-guide.md)
- [Runtime Data](Development/runtime-data.md)
- [Tools Catalog](Development/tools-catalog.md)
- [UI Prototypes](Development/ui-prototypes.md)

## API

- [v3 API Reference](API/README.md)

## Security

- [Security Policy](../SECURITY.md)
- [Security Audit History](SECURITY_AUDIT_REPORT.md)
- [Security Remediation History](SECURITY_REMEDIATION_REPORT.md)

## History

- [UI Lineage](History/ui-lineage.md)
- [Archive](../archive/README.md)
- [Duplicate/Superseded Material](Dup/README.md)

## Research boundary

The [Research](Research/) directory contains concept and study material. It is intentionally outside the operational product-documentation path and does not define current software or hardware behavior.

## Generated material

The [generated](generated/) directory and metrics files contain point-in-time reports, inventories, and audits. They are useful evidence but must not override current source code, tests, or Current documentation.

## Documentation authority

When information conflicts, prefer:

1. current source code and tests;
2. current v3 documentation;
3. root installation/release/security/contribution documents;
4. historical/reference material;
5. generated snapshots.

Last reviewed: 2026-09-20.
