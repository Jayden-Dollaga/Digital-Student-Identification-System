# Documentation Index

This is the active documentation index for the maintained DSIS v3 HTML/pywebview application.

## Source-of-truth rules

When documentation differs from the code, the code wins. The maintained runtime is the v3 desktop app started by `run_web_gui.py`; older v1 and v2 UI material is archived and not treated as the supported operating path.

## Overview

- [Project overview](Overview/project-overview.md)
- [Version history](Overview/version-history.md)
- [Archive boundary](../archive/README.md)

## Architecture

- [v3 system architecture](Architecture/v3-system-architecture.md)
- [pywebview bridge](Architecture/pywebview-bridge.md)
- [Database schema](Architecture/database-schema.md)
- [Data and settings](Architecture/data-and-settings.md)
- [Software flow](Architecture/software-flow.md)

## User Guide

- [Workflows](UserGuide/workflows.md)
- [Enrollment and scanning](UserGuide/enrollment-and-scanning.md)
- [Attendance rules](UserGuide/attendance-rules.md)
- [Roles and permissions](UserGuide/roles-and-permissions.md)
- [Backup, restore, and export](UserGuide/backup-restore-export.md)
- [First-run wizard](UserGuide/first-run-wizard.md)

## Hardware

- [Wiring](Hardware/wiring.md)
- [Firmware](Hardware/firmware.md)
- [Serial protocol](Hardware/serial-protocol.md)
- [Drivers and ports](Hardware/drivers-and-ports.md)

## Development and release

- [Developer setup](Development/setup.md)
- [Testing](Development/testing.md)
- [Release and portable build](Development/release-and-portable-build.md)
- [Logging](Development/logging.md)
- [Change log](Development/change-log.md)

## Troubleshooting and security

- [Desktop troubleshooting](Troubleshooting/desktop.md)
- [Serial and device troubleshooting](Troubleshooting/serial-and-device.md)
- [Database troubleshooting](Troubleshooting/database.md)
- [Security model](Security/security-model.md)

## Reference and generated material

- [Application inventory](generated/APP_INVENTORY.md)
- [root installation guide](../INSTALLATION.md)
- [root portable build guide](../PORTABLE_BUILD.md)
- [root security policy](../SECURITY.md)
- [root release guide](../RELEASE.md)

## Overall authority

When documents disagree, prefer the current code and tests, then the active v3 docs in this tree, then the root installation/release/security guides, and finally historical archive files.
