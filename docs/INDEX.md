# DSIS Documentation Index

This is the single catalog for maintained product documentation and retained textual records. The maintained product is the v3 HTML/pywebview desktop application launched by `run_web_gui.py` or `run_web_gui.bat`, with firmware from `firmware/ESP32_DSIS_AllInOne/`. The complete source-backed runtime inventory is [Application Inventory](generated/APP_INVENTORY.md).

## Authority

When claims conflict, use current source and focused tests first, then the current guides below, then root installation/release/security policies, and finally historical, generated, research, or archived records. Historical files are preserved as snapshots and must not be presented as current implementation guidance.

## Start Here

| Need | Guide |
| --- | --- |
| Install or prepare an operator workstation | [Installation guide](../INSTALLATION.md) and [detailed user installation](UserGuide/installation-guide.md) |
| Operate DSIS | [v3 workflows](UserGuide/v3-workflows.md) |
| Understand system boundaries | [v3 system architecture](Architecture/v3-system.md) |
| Inspect all bridge methods and checks | [Application inventory](generated/APP_INVENTORY.md) and [API reference](API/README.md) |
| Prepare or troubleshoot hardware | [Wiring](Hardware/wiring.md), [firmware](Hardware/firmware.md), [serial protocol](Hardware/serial-protocol.md) |
| Review data and permissions | [Database schema](Architecture/database-schema.md), [runtime data](Architecture/data-and-settings.md), [security model](Security/security-model.md), [roles and permissions](UserGuide/roles-and-permissions.md) |
| Develop, test, or package | [Developer setup](Development/setup.md), [testing](Development/testing.md), [release and portable build](Development/release-and-portable-build.md) |
| Recover from a problem | [Troubleshooting index](Troubleshooting/README.md) |
| Review project evolution | [UI lineage](History/ui-lineage.md) |

## Root Project Guides

- [Project README](../README.md)
- [Installation](../INSTALLATION.md)
- [Portable build](../PORTABLE_BUILD.md)
- [Release process](../RELEASE.md)
- [Security policy](../SECURITY.md)
- [Contributing](../CONTRIBUTING.md)
- [Code of Conduct](../CODE_OF_CONDUCT.md)

## Current Product Guides

### Overview and operations

- [Product overview](Overview/project-overview.md)
- [Version history](Overview/version-history.md)
- [User guide index](UserGuide/README.md)
- [Installation and daily use](UserGuide/installation-guide.md)
- [v3 workflows](UserGuide/v3-workflows.md)
- [Enrollment and scanning](UserGuide/enrollment-and-scanning.md)
- [Attendance rules](UserGuide/attendance-rules.md)
- [Roles and permissions](UserGuide/roles-and-permissions.md)
- [First-run wizard](UserGuide/first-run-wizard.md)
- [Backup, restore, and export](UserGuide/backup-restore-export.md)
- [User-facing project overview](UserGuide/project-overview.md)
- [Documented testing results](UserGuide/testing-results.md)
- [Legacy workflow reference](UserGuide/workflows.md), retained for comparison; check its version scope before applying.

### Architecture and API

- [Architecture index](Architecture/README.md)
- [v3 system](Architecture/v3-system.md)
- [v3 system architecture](Architecture/v3-system-architecture.md)
- [Detailed v3 system architecture](Architecture/v3-system-architecture-detail.md)
- [System architecture](Architecture/system-architecture.md)
- [Architecture overview](Architecture/architecture.md)
- [Software flow](Architecture/software-flow.md)
- [Runtime contract](Architecture/runtime-contract.md)
- [Data and settings](Architecture/data-and-settings.md)
- [Database schema](Architecture/database-schema.md)
- [pywebview bridge contract](Architecture/pywebview-bridge.md)
- [Bridge API reference](Architecture/pywebview-bridge-api-reference.md)
- [Complete system architecture](Architecture/complete-system-architecture.md)
- [End-to-end architecture](Architecture/dsis-end-to-end-architecture.md)
- [API reference](API/README.md)
- [Whole-application inventory](generated/APP_INVENTORY.md)
- [UI map inventory](generated/APP_INVENTORY_UI_MAP.md)

### Hardware

- [Hardware index](Hardware/README.md)
- [Hardware connections](Hardware/hardware-connections.md)
- [Wiring](Hardware/wiring.md)
- [Maintained firmware](Hardware/firmware.md)
- [Firmware variants and historical sketches](Hardware/firmware-variants.md)
- [ESP32 serial protocol](Hardware/serial-protocol.md)
- [Drivers and ports](Hardware/drivers-and-ports.md)

### Development, testing, and operations

- [Development index](Development/README.md)
- [Developer setup](Development/setup.md)
- [Testing](Development/testing.md)
- [Release and portable build](Development/release-and-portable-build.md)
- [Change log](Development/change-log.md)
- [Source file overview](Development/FILES_OVERVIEW.md)
- [Detailed Python file reference](Development/FILES_DETAILED.md)
- [Database updates](Development/database-updates.md)
- [Runtime data](Development/runtime-data.md)
- [Logging guide](Development/logging-guide.md)
- [Logging reference](Development/logging.md)
- [Tools catalog](Development/tools-catalog.md)
- [UI prototypes](Development/ui-prototypes.md)
- [Documentation authority](Development/documentation-authority.md)
- [Documentation map](Development/documentation-map.md)
- [Documentation manifest](Development/documentation-manifest.md)
- [Portable Python notes](Development/PORTABLE_PYTHON.md)
- [Security model](Security/security-model.md)
- [Troubleshooting index](Troubleshooting/README.md)
- [Desktop troubleshooting](Troubleshooting/desktop.md)
- [Serial and device troubleshooting](Troubleshooting/serial-and-device.md)
- [Database troubleshooting](Troubleshooting/database.md)
- [Extended troubleshooting reference](TROUBLESHOOTING.md)

## Retained Historical and Supporting Documents

These records are retained, not silently rewritten. Their findings and plans apply to the snapshot or context recorded in each file, not automatically to the current product.

### Historical, investigations, and implementation notes

- [Documentation overhaul record](Documentation-Overhaul.md), snapshot dated 2026-09-20
- [UI lineage](History/ui-lineage.md)
- [History index](History/README.md)
- [Enrollment regression diagnostic](ENROLLMENT_REGRESSION_DIAGNOSTIC.md)
- [Regression investigation summary](REGRESSION_INVESTIGATION_SUMMARY.md)
- [Root-cause analysis](ROOT_CAUSE_ANALYSIS.md)
- [Historical security audit](SECURITY_AUDIT_REPORT.md)
- [Historical security remediation](SECURITY_REMEDIATION_REPORT.md)
- [Database integration summary](Development/database-integration-summary.md)
- [Legacy fingerprint firmware explanation](Development/ESP32_Fingerprint_AllInOne_firmware_explanation.md)
- [Implementation summary](Development/implementation-summary.md)
- [Legacy logger usage](Development/logger_usage.md)
- [Logging quick reference](Development/logging-quick-reference.md)
- [Logging summary](Development/logging-summary.md)
- [Database migration example](Development/migration-example.md)
- [Polish phase completion notes](Development/polish-phase-complete.md)
- [Polish phase roadmap](Development/polish-phase-roadmap.md)
- [Shutdown crash investigation](Development/SHUTDOWN_CRASH.md)
- [Development TODO](Development/todo.md)
- [Legacy structure notes](Development/structure.txt)
- [Documentation inbox](_inbox/README.md)
- [Duplicate-document notes](Dup/README.md)

### Research and concepts

- [Research concept paper](Research/DSIS_CONCEPT_PAPER.md)
- [Concept-paper source notes](Research/DSIS_CONCEPT_PAPER_SOURCE_NOTES.md)

### Generated snapshots and metrics

Generated files are evidence snapshots; regenerate them deliberately and compare them to current source before relying on behavior claims.

The generated [project forensic audit](generated/PROJECT_FORENSIC_AUDIT.md) is retained as a dated snapshot and currently contains unresolved links to removed or relocated source paths. Its findings and paths are not a current source map.

- [Generated documentation index](generated/INDEX.md)
- [Generated reports index](generated/README.md)
- [Generated architecture](generated/ARCHITECTURE.md)
- [Generated database report](generated/DATABASE.md)
- [Generated file inventory](generated/FILE_INVENTORY.md)
- [Generated firmware report](generated/FIRMWARE.md)
- [Generated GUI report](generated/GUI.md)
- [Generated forensic audit](generated/PROJECT_FORENSIC_AUDIT.md)
- [Generated project overview](generated/PROJECT_OVERVIEW.md)
- [Generated repository audit](generated/REPOSITORY_AUDIT.md)
- [Generated serial protocol report](generated/SERIAL_PROTOCOL.md)
- [Generated testing report](generated/TESTING.md)
- [Generated architecture tree](generated/PROJECT_ARCHITECTURE_TREE.md)
- [Generated visual architecture tree](generated/PROJECT_ARCHITECTURE_VISUAL_TREE.md)
- [Code metrics summary](CODE_METRICS.md)
- [Code metrics CSV](CODE_METRICS.csv)
- [Audit file inventory CSV](audit_file_inventory.csv)

## Catalog and Retention

- [Documentation inventory and classifications](Documentation-Inventory.md)
- [Documentation overview](README.md)
- [Additional retained notes](notes.txt)

Screenshots and other binary assets under `UserGuide/images/` are supporting UI evidence, not independent guides. Archived UI implementations and diagnostic material under `archive/` are outside this docs catalog; see the [archive README](../archive/README.md).
