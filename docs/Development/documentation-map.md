# Documentation Map

This map separates current operational guidance from historical and generated material.

## Current guidance

- `../README.md`: full v3 system architecture and runtime contract.
- `../UserGuide/v3-workflows.md`: enrollment, scanning, evaluation, settings, permissions, backup, restore, and hardware workflows.
- `../Architecture/v3-system.md`: component boundaries and application flow.
- `../Hardware/`: ESP32, AS608, wiring, firmware variants, and serial requirements.
- `../Troubleshooting/README.md`: concise current recovery and diagnostics.
- `../Development/FILES_OVERVIEW.md`: current source-tree map.
- `../Development/FILES_DETAILED.md`: current Python module guide.
- `../Development/PORTABLE_PYTHON.md`: portable runtime guidance.
- `../Development/change-log.md`: release history and unreleased development entries.
- `../../PORTABLE_BUILD.md`: current PyInstaller build process.
- `../../CONTRIBUTING.md`: contribution and validation requirements.
- `../../RELEASE.md`: release checklist and versioning policy.
- `../../SECURITY.md`: vulnerability reporting and supported-version policy.

## Historical material

- `../History/`: curated v1/v2/v3 evolution notes.
- `../../archive/legacy-ui/v1/`: historical CustomTkinter application.
- `../../archive/legacy-ui/v2/`: historical PySide6/Qt application.
- `../Dup/`: preserved duplicates and superseded investigations.
- `../Research/`: concept and research material, not runtime guarantees.

## Generated material

`../generated/` contains point-in-time audits, metrics, inventories, and forensic reports. They are evidence snapshots and may contain paths or architecture descriptions that were true when generated but are no longer current. Do not use them as installation instructions.

## Validation rule

When documentation conflicts, prefer this order:

1. Active source code and tests at the current commit.
2. Current guidance listed above.
3. Tagged release documentation.
4. Archive and generated reports as historical evidence.

Last reviewed: 2026-09-11, against commit `aa457e0`.
