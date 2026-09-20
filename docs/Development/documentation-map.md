# DSIS Documentation Map

This map defines the role of each documentation area and which material should be treated as authoritative for the maintained v3 application.

## Source-of-truth order

1. Current source code and automated tests.
2. Current v3 documentation.
3. Root installation/release/security/contribution documents.
4. Historical/reference documents.
5. Generated reports and snapshots.

Generated or historical material must not override current implementation behavior.

## Current product documentation

| Area | Purpose | Primary references |
| --- | --- | --- |
| Root | Public project entry point and deployment policies | `README.md`, `INSTALLATION.md`, `PORTABLE_BUILD.md` |
| Architecture | Internal design and runtime behavior | `Architecture/v3-system.md`, `Architecture/system-architecture.md`, `Architecture/software-flow.md`, `Architecture/database-schema.md` |
| Hardware | ESP32/AS608 wiring and firmware | `Hardware/hardware-connections.md`, `Hardware/wiring.md`, `Hardware/firmware-variants.md` |
| UserGuide | Installation, operation, and validation | `UserGuide/installation-guide.md`, `UserGuide/v3-workflows.md`, `UserGuide/project-overview.md`, `UserGuide/testing-results.md` |
| Troubleshooting | Current recovery procedures | `Troubleshooting/README.md`, `TROUBLESHOOTING.md` |
| Development | Source maps, database, logs, runtime data, prototypes | `Development/FILES_DETAILED.md`, `database-updates.md`, `logging-guide.md`, `runtime-data.md`, `ui-prototypes.md` |
| API | Browser-to-Python bridge reference | `API/README.md` |

## Research boundary

`Research/` contains concept-paper and research material. It is intentionally outside the operational product documentation path.

Research may explain why DSIS was proposed, its study context, or future concepts, but it does not define current software or hardware behavior.

## Historical boundary

`History/`, `Dup/`, legacy UI directories, old investigation reports, and old implementation notes preserve project evolution or troubleshooting provenance. They should be treated as historical when their behavior differs from v3.

## Generated boundary

`generated/`, metrics, inventories, and audit snapshots are point-in-time evidence. Regenerate them deliberately and direct readers back to current documentation for runtime behavior.

## Documentation quality rules

Current technical documents should include, where relevant:

- purpose and scope;
- exact paths and commands;
- current defaults and protocol values;
- prerequisites and failure conditions;
- examples or diagrams for non-obvious behavior;
- links to source-of-truth implementation files;
- a review date.

Do not document a behavior as current merely because it existed in v1/v2 or in a generated report.

## Current application boundary

The maintained runtime is `run_web_gui.py` / `run_web_gui.bat` -> `python/gui_web/` -> `python/core/` + local data -> ESP32/AS608.

Legacy Qt/CustomTkinter code and UI prototypes are not current launchers.

Last reviewed: 2026-09-20.