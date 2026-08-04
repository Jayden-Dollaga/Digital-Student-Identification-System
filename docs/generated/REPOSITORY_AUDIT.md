# Repository Audit

## High-level structure

- `README.md` — project overview, install instructions, usage notes.
- `requirements.txt` — Python dependencies.
- `install_requirements.bat` — Windows setup helper.
- `run_app.bat` — starts the legacy CustomTkinter GUI.
- `run_qt_gui.py` / `run_qt_gui.bat` — starts the modern Qt GUI.
- `firmware/` — ESP32 sketches and firmware sources.
- `python/` — Python application code.
- `data/` — runtime data storage, backups, exports.
- `docs/` — existing documentation and generated audit output.
- `tests/` — regression and GUI tests.
- `tools/` — build and packaging helpers.

## Notable existing docs

- `docs/Architecture/architecture.md`
- `docs/Architecture/database-schema.md`
- `docs/Architecture/software-flow.md`
- `docs/Architecture/system-architecture.md`
- `docs/Development/FILES_OVERVIEW.md`
- `docs/Development/FILES_DETAILED.md`
- `docs/Development/implementation-summary.md`
- `docs/Development/migration-example.md`
- `docs/Development/polish-phase-roadmap.md`

## Generated audit artifacts

This repository audit adds the following generated documents:

- `docs/generated/PROJECT_OVERVIEW.md`
- `docs/generated/ARCHITECTURE.md`
- `docs/generated/FIRMWARE.md`
- `docs/generated/SERIAL_PROTOCOL.md`
- `docs/generated/GUI.md`
- `docs/generated/DATABASE.md`
- `docs/generated/TESTING.md`

## Gaps and next steps

- `tools/` contents should be audited in detail if packaging or build automation is a priority.
- `docs/UserGuide/` and `docs/Hardware/` may contain user-facing guidance that should be reconciled with the generated docs.
- The legacy and Qt GUI stacks would benefit from a unified component map.
- A future audit could also document the exact database schema SQL and the test coverage metrics.
