# DSIS Documentation Inventory

This file is the complete Markdown documentation inventory for commit `3f42ccc` (2026-09-19). Every Markdown file in the repository is classified below so reviewers can distinguish current guidance from historical, generated, research, duplicate, cache, and reference material.

## Classification rules

- **Current**: intended to describe the maintained v3 application and current development workflow.
- **Historical**: preserves v1/v2 behavior, old plans, investigations, or previous implementation state.
- **Generated**: point-in-time reports or inventories; not authoritative for current behavior.
- **Reference**: useful source, research, legal, community, or dependency material.
- **Archive**: preserved UI or experiment documentation; not part of the supported runtime.
- **Cache**: generated tool/cache material; not project documentation.

When documents conflict, prefer current source code and tests, then Current documents, then release documentation, then Historical/Generated material.

## Current root documentation

- `README.md` — Current product overview, v3 quick start, hardware drivers, launchers, and documentation links.
- `INSTALLATION.md` — Current Windows installation, `.venv` installer behavior, firmware prerequisites, and hardware setup.
- `PORTABLE_BUILD.md` — Current `Build/DSIS_v3.spec` PyInstaller workflow and packaged-output validation.
- `CONTRIBUTING.md` — Branch, commit, pull-request, validation, and source-of-truth guidance.
- `RELEASE.md` — Versioning, packaging, hardware validation, and release checklist.
- `SECURITY.md` — Vulnerability reporting and supported release/main-branch policy.
- `CODE_OF_CONDUCT.md` — Community conduct policy.

## Current docs navigation and architecture

- `docs/INDEX.md` — Primary documentation navigation.
- `docs/README.md` — Documentation orientation.
- `docs/Documentation-Overhaul.md` — Reorganization manifest and source-of-truth summary.
- `docs/Documentation-Inventory.md` — This complete file-by-file classification.
- `docs/Architecture/v3-system.md` — Authoritative v3 architecture, bridge, flow, synchronization, permissions, and data behavior.
- `docs/Architecture/system-architecture.md` — Layered architecture reference, updated to v3.
- `docs/Architecture/software-flow.md` — Runtime, enrollment, scanning, backup, permissions, and evaluation flow.
- `docs/Architecture/database-schema.md` — SQLite schema, foreign keys, event types, and reserved unknown-scan row.

## Current hardware and user guides

- `docs/Hardware/hardware-connections.md` — ESP32/AS608 hardware overview and exact wiring.
- `docs/Hardware/wiring.md` — Pin, baud, and module-power guidance.
- `docs/Hardware/firmware-variants.md` — Maintained all-in-one firmware and historical sketches.
- `docs/UserGuide/v3-workflows.md` — Current connection, enrollment, scanning, evaluation, permissions, settings, backup, restore, and hardware workflows.
- `docs/UserGuide/installation-guide.md` — Detailed Windows/Arduino/driver installation guide.
- `docs/UserGuide/project-overview.md` — Current product, architecture, UI, data, and role overview.
- `docs/UserGuide/testing-results.md` — Current automated and hardware-validation status.
- `docs/Troubleshooting/README.md` — Current concise troubleshooting and recovery guide.
- `docs/TROUBLESHOOTING.md` — Longer troubleshooting reference.

## Current development documentation

- `docs/Development/documentation-map.md` — Current, historical, and generated navigation rules.
- `docs/Development/FILES_OVERVIEW.md` — Current source-tree overview.
- `docs/Development/FILES_DETAILED.md` — Current v3 Python module guide.
- `docs/Development/change-log.md` — Feature and maintenance history through current work.
- `docs/Development/database-updates.md` — Current database initialization, migration, and backup notes.
- `docs/Development/implementation-summary.md` — Current implementation summary and verification notes.
- `docs/Development/logging-guide.md` — Active logging behavior and troubleshooting guidance.
- `docs/Development/PORTABLE_PYTHON.md` — Portable Python and `.venv` guidance.
- `docs/Development/runtime-data.md` — Runtime data sensitivity, retention, and storage policy.
- `docs/Development/tools-catalog.md` — Developer tools and audit generators.
- `docs/Development/ui-prototypes.md` — Isolated visual prototypes and their non-production scope.

## Historical development and investigation documents

These files are preserved for provenance. They may describe old UI frameworks, old paths, old test counts, or unfinished plans and must not override current guides.

- `docs/Development/database-integration-summary.md`
- `docs/Development/ESP32_Fingerprint_AllInOne_firmware_explanation.md`
- `docs/Development/logger_usage.md`
- `docs/Development/logging-quick-reference.md`
- `docs/Development/logging-summary.md`
- `docs/Development/migration-example.md`
- `docs/Development/polish-phase-complete.md`
- `docs/Development/polish-phase-roadmap.md`
- `docs/Development/SHUTDOWN_CRASH.md`
- `docs/Development/structure.txt`
- `docs/Development/todo.md`
- `docs/ENROLLMENT_REGRESSION_DIAGNOSTIC.md`
- `docs/REGRESSION_INVESTIGATION_SUMMARY.md`
- `docs/ROOT_CAUSE_ANALYSIS.md`
- `docs/SECURITY_AUDIT_REPORT.md`
- `docs/SECURITY_REMEDIATION_REPORT.md`

## History, archive, research, and reference

- `docs/History/ui-lineage.md` — Curated v1 CustomTkinter, v2 Qt, and v3 webview lineage.
- `docs/Dup/README.md` — Preserved duplicate/superseded material.
- `docs/Research/DSIS_CONCEPT_PAPER.md` — Research/concept paper.
- `docs/Research/DSIS_CONCEPT_PAPER_SOURCE_NOTES.md` — Concept-paper source notes.
- `docs/_inbox/README.md` — Image/documentation inbox instructions.
- `archive/README.md` — Archive policy and legacy UI boundaries.
- `archive/legacy-ui/v1/README.md` — Historical v1 CustomTkinter UI.
- `archive/legacy-ui/v2/README.md` — Historical v2 PySide6/Qt UI.
- `archive/legacy-ui/gui_qt_redesign/README.md` — Historical Qt redesign scaffold.
- `archive/legacy-ui/gui_qt_redesign_2/README.md` — Historical Qt redesign variant.
- `python/gui_web/v2_reference/README.md` — Reference-only v2 implementation snapshot.
- `system/python/README.md` — Portable runtime reference.
- `tests/README_QT_GUI_TEST.md` — Historical v2 Qt smoke-test guide.
- `tests/TEST_GUI_README.md` — Test GUI reference material.

## Generated snapshots

These files are generated or point-in-time audits. Their paths, test counts, UI descriptions, and inventories may be stale and should not be used as current setup instructions.

- `docs/CODE_METRICS.md`
- `docs/generated/ARCHITECTURE.md`
- `docs/generated/DATABASE.md`
- `docs/generated/FILE_INVENTORY.md`
- `docs/generated/FIRMWARE.md`
- `docs/generated/GUI.md`
- `docs/generated/INDEX.md`
- `docs/generated/PROJECT_FORENSIC_AUDIT.md`
- `docs/generated/PROJECT_OVERVIEW.md`
- `docs/generated/REPOSITORY_AUDIT.md`
- `docs/generated/SERIAL_PROTOCOL.md`
- `docs/generated/TESTING.md`

## Cache and generated non-project material

- `.pytest_cache/README.md` — pytest cache documentation; not project guidance.

## Code-level documentation scope

The implementation audit also covered module docstrings, build comments, firmware comments, and API comments. Current source documentation is concentrated in `python/gui_web/api.py`, `python/gui_web/main_web.py`, `python/core/`, `python/config.py`, `python/settings_store.py`, `Build/DSIS_v3.spec`, and the maintained firmware sketch. Archived v1/v2 source comments remain historical by design.

Last reviewed: 2026-09-19, against commit `3f42ccc`.
