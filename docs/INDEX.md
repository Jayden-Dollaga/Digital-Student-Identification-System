# Documentation Index

Use this page to find current v3 guidance and clearly labeled historical or generated material.

Start with the [documentation map](Development/documentation-map.md), the [v3 workflow guide](UserGuide/v3-workflows.md), or the [v3 architecture](Architecture/v3-system.md).

## Top-level sections

- [Architecture](Architecture/architecture.md)
- [Database schema](Architecture/database-schema.md)
- [Software flow](Architecture/software-flow.md)
- [System architecture](Architecture/system-architecture.md)
- [v3 system architecture](Architecture/v3-system.md)
- [Hardware](Hardware/hardware-connections.md)
- [Wiring](Hardware/wiring.md)
- [Firmware variants](Hardware/firmware-variants.md)
- [User guide](UserGuide/project-overview.md)
- [Installation](UserGuide/installation-guide.md)
- [Testing results](UserGuide/testing-results.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Current troubleshooting](Troubleshooting/README.md)
- [Development changelog](Development/change-log.md)
- [Contributing](../CONTRIBUTING.md)
- [Release guide](../RELEASE.md)
- [Database updates](Development/database-updates.md)
- [Logging guide](Development/logging-guide.md)
- [Portable Python](Development/PORTABLE_PYTHON.md)
- [UI prototypes](Development/ui-prototypes.md)
- [Tools catalog](Development/tools-catalog.md)
- [Runtime data](Development/runtime-data.md)
- [Development TODO](Development/todo.md)
- [Documentation map](Development/documentation-map.md)
- [UI lineage](History/ui-lineage.md)
- [Security audit](SECURITY_AUDIT_REPORT.md)
- [Security remediation status](SECURITY_REMEDIATION_REPORT.md)
- [Root security disclosure policy](../SECURITY.md)
- [Code of Conduct](../CODE_OF_CONDUCT.md)
- [License](../LICENSE)
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
- `Troubleshooting/` — concise current recovery and diagnostic guidance.
- `Development/` — developer notes, change logs, implementation details, and project tracking.
- `History/` — curated v1/v2/v3 evolution notes.
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

Last reviewed: 2026-09-11, against commit `aa457e0`
