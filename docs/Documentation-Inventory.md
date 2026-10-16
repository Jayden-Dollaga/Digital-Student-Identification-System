# Documentation Inventory

This page classifies retained project documentation. [The documentation index](INDEX.md) is the complete link catalog for retained textual docs and audit artifacts. The source-backed [application inventory](generated/APP_INVENTORY.md) records the maintained runtime, API, permissions, persistence, firmware, and tests.

## Authority

1. Current checked-out source and focused tests define behavior.
2. The current operator, architecture, hardware, development, troubleshooting, security, and API guides linked from [INDEX.md](INDEX.md) explain that behavior.
3. Root `README.md`, `INSTALLATION.md`, `PORTABLE_BUILD.md`, `RELEASE.md`, `SECURITY.md`, and `CONTRIBUTING.md` provide project entry and policy guidance.
4. History, investigations, research, generated reports, prototypes, and archived implementations are preserved evidence. Their claims are scoped to their date, commit, or earlier product version.

Do not treat an old report as a current implementation guarantee. Where any current guide conflicts with source/tests, correct the guide; do not rewrite historical findings to make them appear current.

## Maintained Product

The maintained desktop application is the HTML/pywebview v3 runtime launched by `run_web_gui.py` or `run_web_gui.bat`. The active UI is under `python/gui_web/web/`; its Python bridge is `python/gui_web/api.py`; shared behavior is in `python/core/`, `python/services/`, `python/config.py`, and `python/settings_store.py`. The maintained firmware is `firmware/ESP32_DSIS_AllInOne/ESP32_DSIS_AllInOne.ino` and its `src/rfid/` adapters.

The v1 CustomTkinter and v2 Qt applications, `python/gui/legacy/`, `python/gui_web/v2_reference/`, standalone/diagnostic firmware, old package outputs, and `tests/Prototype/` are historical or experimental, not alternate supported v3 launch paths. See [archive README](../archive/README.md) and [UI lineage](History/ui-lineage.md).

## Documentation Classes

| Class | Meaning | Location examples |
| --- | --- | --- |
| Current product guidance | Current operational, architectural, hardware, development, and security behavior; verify against source/tests | `UserGuide/`, `Architecture/`, `Hardware/`, `Development/`, `Troubleshooting/`, `Security/`, `API/` |
| Root policy and onboarding | Canonical project entry, install, release, contribution, and security policy | repository root guides listed above |
| Historical or investigative | Records prior implementation behavior, regressions, security reviews, or plans; not current authority | `History/`, dated diagnostics, security reports, prior phase notes |
| Generated snapshot | Generated inventory, metrics, architecture, test, or forensic snapshot; may become stale | `generated/`, metrics and inventory outputs |
| Research | Study and concept material; not runtime requirements | `Research/` |
| Preserved duplicate or intake | Superseded duplicate notes or unprocessed documentation assets | `Dup/`, `_inbox/` |
| Binary supporting asset | Screenshot or image illustrating a UI snapshot; not an independent procedure | `UserGuide/images/` |

## Canonical Current References

- [Documentation index](INDEX.md)
- [Application inventory](generated/APP_INVENTORY.md)
- [v3 system architecture](Architecture/v3-system.md)
- [Database schema](Architecture/database-schema.md)
- [Full API reference](API/README.md)
- [User workflows](UserGuide/v3-workflows.md)
- [Roles and permissions](UserGuide/roles-and-permissions.md)
- [Maintained firmware](Hardware/firmware.md)
- [Serial protocol](Hardware/serial-protocol.md)
- [Security model](Security/security-model.md)
- [Developer testing](Development/testing.md)
- [Troubleshooting](Troubleshooting/README.md)

## Completeness and Maintenance

The index links all retained Markdown, plain-text, and CSV documents in `docs/`. It does not enumerate individual screenshots, other binary assets, generated build outputs, or archived source files. Update `INDEX.md` when adding, moving, or removing a textual document. Update the closest current guide and the application inventory whenever a maintained public surface, data contract, permission, or hardware protocol changes.

Last reviewed: 2026-10-16.
