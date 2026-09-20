# DSIS Documentation Inventory

This inventory classifies the repository's documentation so readers can distinguish current v3 guidance from historical, generated, research, duplicate, cache, and reference material.

## Classification

| Class | Meaning |
| --- | --- |
| Current | Describes the maintained v3 implementation or current development/release process |
| Historical | Preserves earlier implementation behavior, investigations, or plans |
| Generated | Point-in-time audit/metric/inventory output |
| Research | Concept/study material; not a runtime contract |
| Archive | Preserved legacy UI or experiment documentation |
| Reference | Supporting material that does not define runtime behavior |
| Cache | Tool/cache material; not project documentation |

When documentation conflicts, prefer current source code and tests, then Current documents, then root release/deployment/security documents, then Historical/Generated material.

## Current root documentation

- README.md — Product overview and navigation
- INSTALLATION.md — Current Windows/source installation and firmware setup
- PORTABLE_BUILD.md — Current v3 PyInstaller build workflow
- CONTRIBUTING.md — Contribution and validation rules
- RELEASE.md — Release procedure
- SECURITY.md — Security reporting and supported-version policy
- CODE_OF_CONDUCT.md — Community conduct

## Current docs navigation

- docs/README.md — Documentation orientation
- docs/INDEX.md — Main documentation index
- docs/Documentation-Overhaul.md — Documentation architecture and accuracy corrections
- docs/Documentation-Inventory.md — This classification

## Current architecture

- docs/Architecture/v3-system.md — Authoritative v3 runtime architecture
- docs/Architecture/system-architecture.md — Architectural component reference
- docs/Architecture/software-flow.md — Startup, discovery, enrollment, scan, evaluation, wipe, backup, and shutdown flow
- docs/Architecture/database-schema.md — SQLite schema, validation, migration, and data relationships

## Current hardware

- docs/Hardware/hardware-connections.md — Hardware overview and exact connections
- docs/Hardware/wiring.md — GPIO, UART, power, and board notes
- docs/Hardware/firmware-variants.md — Current firmware metadata, protocol, commands, and historical sketches

## Current user guides

- docs/UserGuide/project-overview.md — Product, data model, architecture, and security overview
- docs/UserGuide/installation-guide.md — Detailed Windows installation and daily-use setup
- docs/UserGuide/v3-workflows.md — Operator workflow reference
- docs/UserGuide/testing-results.md — Documented software/hardware validation
- docs/Troubleshooting/README.md — Current recovery guide
- docs/TROUBLESHOOTING.md — Longer diagnostic reference

## Current development documentation

- docs/Development/documentation-map.md — Source-of-truth and documentation boundaries
- docs/Development/FILES_OVERVIEW.md — Current repository/source-tree overview
- docs/Development/FILES_DETAILED.md — Active Python module reference
- docs/Development/database-updates.md — SQLite maintenance and migration
- docs/Development/logging-guide.md — Logging behavior and diagnostics
- docs/Development/runtime-data.md — Runtime storage and retention
- docs/Development/tools-catalog.md — Developer/diagnostic tools
- docs/Development/ui-prototypes.md — Prototype scope and execution

## API documentation

- docs/API/README.md — Current JavaScript-to-Python bridge and public Api method reference

## Historical and investigation documents

These are retained for provenance and should not override current v3 behavior:

- docs/History/ui-lineage.md
- docs/Development/database-integration-summary.md
- docs/Development/ESP32_Fingerprint_AllInOne_firmware_explanation.md
- docs/Development/logger_usage.md
- docs/Development/logging-quick-reference.md
- docs/Development/logging-summary.md
- docs/Development/migration-example.md
- docs/Development/polish-phase-complete.md
- docs/Development/polish-phase-roadmap.md
- docs/Development/SHUTDOWN_CRASH.md
- docs/Development/structure.txt
- docs/Development/todo.md
- docs/ENROLLMENT_REGRESSION_DIAGNOSTIC.md
- docs/REGRESSION_INVESTIGATION_SUMMARY.md
- docs/ROOT_CAUSE_ANALYSIS.md

## Security reports

Security audit/remediation files are historical evidence of findings and fixes. Use them together with the current SECURITY.md and current source:

- docs/SECURITY_AUDIT_REPORT.md
- docs/SECURITY_REMEDIATION_REPORT.md

## Generated documents

Generated metrics, inventories, forensic audits, and generated architecture/database/testing reports are snapshots. They should be regenerated deliberately and must not be treated as the authoritative runtime contract:

- docs/CODE_METRICS.md
- docs/generated/ARCHITECTURE.md
- docs/generated/DATABASE.md
- docs/generated/FILE_INVENTORY.md
- docs/generated/FIRMWARE.md
- docs/generated/GUI.md
- docs/generated/INDEX.md
- docs/generated/PROJECT_FORENSIC_AUDIT.md
- docs/generated/PROJECT_OVERVIEW.md
- docs/generated/REPOSITORY_AUDIT.md
- docs/generated/SERIAL_PROTOCOL.md
- docs/generated/TESTING.md

## Research boundary

docs/Research/ contains concept-paper and study material. It is intentionally excluded from the product documentation path and does not define current implementation behavior.

## Preserved/other material

- docs/Dup/ — duplicates and superseded material
- docs/_inbox/ — documentation asset intake
- archive/ — historical implementations and diagnostics
- python/gui_web/v2_reference/ — v2 reference implementation
- tests/Prototype/ — isolated interface prototypes

## Maintenance rule

Whenever implementation behavior changes, update the nearest Current document in the same change when practical. Include exact paths, commands, defaults, protocol values, failure behavior, and review dates.

Last reviewed: 2026-09-20.
