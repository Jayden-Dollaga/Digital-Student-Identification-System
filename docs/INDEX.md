# Documentation Index

Use this page to find maintained guidance and clearly labeled historical or generated material.

## Top-level sections

- [Architecture](Architecture/architecture.md)
- [Database schema](Architecture/database-schema.md)
- [Software flow](Architecture/software-flow.md)
- [System architecture](Architecture/system-architecture.md)
- [Hardware](Hardware/hardware-connections.md)
- [Wiring](Hardware/wiring.md)
- [Firmware variants](Hardware/firmware-variants.md)
- [User guide](UserGuide/project-overview.md)
- [Installation](UserGuide/installation-guide.md)
- [Testing results](UserGuide/testing-results.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Development changelog](Development/change-log.md)
- [Database updates](Development/database-updates.md)
- [Logging guide](Development/logging-guide.md)
- [Portable Python](Development/PORTABLE_PYTHON.md)
- [Tools catalog](Development/tools-catalog.md)
- [Runtime data](Development/runtime-data.md)
- [Development TODO](Development/todo.md)
- [Security audit](SECURITY_AUDIT_REPORT.md)
- [Security remediation status](SECURITY_REMEDIATION_REPORT.md)
- [Research](Research/)
- [Concept paper](Research/DSIS_CONCEPT_PAPER.md)
- [Concept paper source notes](Research/DSIS_CONCEPT_PAPER_SOURCE_NOTES.md)
- [API](API/)
- [Generated Audit](generated/INDEX.md)
- [Duplicates](Dup/README.md)
- [Archive](../archive/README.md)

## Current folder purpose

- `Architecture/` — system design, data flow, and architecture documentation.
- `Hardware/` — wiring and physical connection documentation.
- `UserGuide/` — installation instructions, usage guidance, and testing results.
- `Development/` — developer notes, change logs, implementation details, and project tracking.
- `Research/` — experimental notes, research findings, and exploratory documentation.
- `API/` — API or interface docs, reserved for future expansion.
- `generated/` — automatically generated audit reports and repository analysis.
- `Dup/` — preserved duplicate files from the legacy docs root.
- `../archive/` — historical diagnostics and superseded UI code; it is not part of the supported runtime.

## Duplicate handling

Confirmed duplicate screenshots are preserved in `Dup/duplicate-screenshots/`.
The canonical copies remain in `UserGuide/images/`.

## Notes

- `docs/Dup/` stores duplicate and superseded artifacts so cleanup is traceable.
- `docs/README.md` gives the short orientation page.
- This file is the primary documentation entry point.

Historical investigation reports retained for review:

- [Enrollment regression diagnostic](ENROLLMENT_REGRESSION_DIAGNOSTIC.md)
- [Enrollment regression summary](REGRESSION_INVESTIGATION_SUMMARY.md)
- [Enrollment root-cause analysis](ROOT_CAUSE_ANALYSIS.md)

Generated reports are listed in [generated/INDEX.md](generated/INDEX.md). Archived
copies and one-off reports are listed in [Dup/README.md](Dup/README.md).

Last verified: 2026-08-28, against commit 3119175
