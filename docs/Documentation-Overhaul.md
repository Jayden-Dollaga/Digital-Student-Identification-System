# DSIS Documentation Overhaul

This manifest records the repository-wide documentation audit and organization reviewed against commit `9ffd69f` on 2026-09-18. It is the entry point for understanding which documents are current, historical, generated, or preserved for research.

## Documentation structure

```text
docs/
├── INDEX.md                         Navigation index
├── README.md                        Documentation orientation
├── Documentation-Overhaul.md        This audit and organization manifest
├── Documentation-Inventory.md        Complete Markdown file classification
├── Architecture/
│   ├── v3-system.md                 Current v3 architecture and bridge flow
│   ├── system-architecture.md       Layered architecture reference
│   ├── software-flow.md             Runtime workflow reference
│   └── database-schema.md           SQLite schema and data rules
├── Hardware/
│   ├── hardware-connections.md      ESP32 and AS608 connections
│   ├── wiring.md                    Pin and power notes
│   └── firmware-variants.md         Maintained and historical firmware
├── UserGuide/
│   ├── v3-workflows.md              Current daily-use workflows
│   ├── installation-guide.md        Full Windows setup guide
│   ├── project-overview.md          Product and feature overview
│   └── testing-results.md           Current automated/manual validation
├── Troubleshooting/
│   └── README.md                    Current concise troubleshooting guide
├── Development/
│   ├── documentation-map.md         Current/historical/generated map
│   ├── FILES_OVERVIEW.md            Current source-tree overview
│   ├── FILES_DETAILED.md            Current Python module guide
│   ├── change-log.md                Feature and release history
│   ├── database-updates.md          Database migration notes
│   ├── implementation-summary.md    Current implementation summary
│   ├── logging-guide.md             Active logging guidance
│   ├── PORTABLE_PYTHON.md           Portable runtime guidance
│   ├── tools-catalog.md             Developer tools
│   ├── ui-prototypes.md             Prototype UI guidance
│   ├── runtime-data.md              Runtime data policy
│   ├── structure.txt                Historical structure tracker
│   └── FILES_DETAILED.md            Historical inventory replacement
├── History/
│   └── ui-lineage.md                v1/v2/v3 evolution
├── generated/                       Point-in-time generated reports
├── Dup/                             Preserved duplicates and investigations
├── Research/                        Concept and research material
├── API/                             Reserved API documentation area
└── _inbox/                          Documentation image inbox
```

Build artifacts are kept outside `docs/` under `Build/`. `Build/DSIS_v3.spec` is the active v3 packaging specification. The checked-in `Build/DSIS_v3/` and `Build/DSIS_v2/` directories contain generated packaged outputs and PyInstaller analysis artifacts; they are deployment artifacts, not source-of-truth implementation files.

## Current source of truth

The maintained application is DSIS v3:

- Launcher: `run_web_gui.py` or `run_web_gui.bat`.
- Native shell: `python/gui_web/main_web.py`.
- Python bridge: `python/gui_web/api.py`.
- Frontend: `python/gui_web/web/index.html`, `app.js`, and `styles.css`.
- Backend: `python/core/` and selected `python/services/` wrappers.
- Storage: SQLite under `data/attendance.db`, JSON settings, backups, logs, exports, and charts.
- Hardware: `firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino` with ESP32 WROOM-32 and AS608.

## Documentation groups

### Current documentation

Root README, installation/build/security/release/contribution files, the v3 architecture and workflow guides, hardware guides, troubleshooting, current file maps, database notes, testing results, and logging/runtime guidance are intended to describe HEAD and must be reviewed when source behavior changes.

### Historical documentation

`History/`, `archive/legacy-ui/`, `docs/Dup/`, historical investigations, old roadmaps, and old implementation reports preserve prior behavior. They must be labeled as historical and must not be used as current installation instructions.

The UI lineage is:

- v1: CustomTkinter under `archive/legacy-ui/v1/`.
- v2: PySide6/Qt under `archive/legacy-ui/v2/` and `python/gui_web/v2_reference/`.
- v3: HTML/CSS/JavaScript in pywebview under `python/gui_web/`.

### Generated documentation

`docs/generated/` contains audit reports, inventories, metrics, and forensic snapshots. These are evidence from their generation point. They may contain old launchers, old UI descriptions, old test counts, runtime files, or stale paths. The generated index explicitly directs readers to current docs for authoritative behavior.

## Covered implementation topics

The current documentation set explains:

- ESP32 and AS608 wiring, power, drivers, and baud rates.
- Device discovery, identity handshake, port ranking, stale-port recovery, reconnects, reset/replug recovery, and fingerprint-count synchronization.
- Enrollment validation, device-assigned IDs, cancellation, disconnect handling, and save-after-success behavior.
- JSON and compatibility text scanning, confidence thresholds, duplicate cooldown, unknown ID 0 persistence, and attendance evaluation.
- Day/week/month evaluation, observed-school-day calculation, categories, sorting, leaderboard behavior, and CSV export permissions.
- SQLite schema, backups, restore validation, local data clearing, logs, charts, reports, and export paths.
- Administrator, teacher, and guest local action gating, with the limitation that roles are not authentication.
- Dedicated `attendance_evaluation` permission for Administrator, Teacher, and Guest roles; the visible v3 Lock button was removed.
- v1/v2/v3 architecture and the pywebview JavaScript-to-Python event bridge.
- Build cleanup in `d3fb362`, `.venv` installation behavior, `Build/DSIS_v3.spec`, and `Build/DSIS_v3` output.
- Build artifact preservation in `64d80c9`, including v2/v3 packaged outputs, PyInstaller analysis files, and `Documentation-Overhaul.md`.
- Student-facing terminology now uses **Student LRN**; CSV headers, enrollment/edit forms, reports, and tables map the existing `student_no` database field to that label.
- Administrator settings save automatically, and **Restore Defaults** resets application settings while preserving authentication and active role state.
- The v3 wipe workflow is presented as metadata cleanup with linked local-data removal; this wording should remain aligned with the API and tests.

## Known gaps

- The latest full test run reports 233 passed, 3 skipped, and 1 attendance-export contract failure where the test expects `Present` but the current implementation returns `Early`.
- Pytest may exit with a Windows GUI teardown status after reporting results; this requires separate CI/runtime investigation.
- Physical ESP32/AS608 validation and clean-machine packaging validation require target hardware and a clean Windows environment.
- Generated reports should be regenerated only after their generators are made reproducible.
- The current v3 refactor removed some symbols expected by older web smoke tests; tests and implementation need a deliberate contract decision.

Last reviewed: 2026-09-18, against commit `9ffd69f`.
