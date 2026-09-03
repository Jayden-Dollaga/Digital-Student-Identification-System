# Generated Documentation Index

This folder contains point-in-time audit artifacts generated from repository analysis. These reports are not automatically kept in sync with `main`; consult the active guides under `docs/` for current behavior.

`CODE_METRICS.md` and `CODE_METRICS.csv` can be regenerated with:

```text
python audit/generate_metrics.py
```

The remaining reports are point-in-time audit outputs. Their generating command
is not currently recorded in the repository and should be verified before being
regenerated.

- `PROJECT_OVERVIEW.md` — summary of project purpose, architecture, workflows, and user scenarios.
- `ARCHITECTURE.md` — component-level architecture audit and service responsibilities.
- `FIRMWARE.md` — detailed firmware sketch behavior, command set, and serial output.
- `SERIAL_PROTOCOL.md` — serial communication protocol, handshake, command flow, and compatibility notes.
- `GUI.md` — audit of both legacy CustomTkinter and modern Qt UI stacks.
- `DATABASE.md` — SQLite schema, persistence behavior, exports, and backup support.
- `TESTING.md` — testing coverage areas and notable regression test files.
- `REPOSITORY_AUDIT.md` — high-level repository structure, existing docs, and recommendations.
- `FILE_INVENTORY.md` — complete file inventory for the repository, including generated and existing documentation.
- `PROJECT_FORENSIC_AUDIT.md` — point-in-time forensic audit of repository structure and project history.

Generated snapshot last verified: 2026-08-28, against commit 3119175
