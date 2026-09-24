# Documentation Authority and Boundaries

This file defines which repository sources control current behavior and how to interpret the rest of the documentation set.

## Authority order

When two sources disagree, use this order:

1. Current executable source and firmware in the checked-out commit.
2. Focused tests that exercise that source.
3. Canonical documents linked from `docs/README.md` and `docs/INDEX.md`.
4. Release and change-history documents, interpreted against their recorded date or commit.
5. Generated inventories, forensic reports, prototypes, and archived material.

A document in a lower category may be valuable evidence without being a current operating instruction.

## Product boundary

DSIS v3 is the maintained application. `run_web_gui.py` launches `python.gui_web.main_web`, which creates a pywebview window over `python/gui_web/web/index.html` and exposes `python/gui_web/api.py` as `window.pywebview.api`. The API delegates to shared modules in `python/core/` and `python/services/`; it does not create a separate web server.

The current hardware path is the maintained all-in-one sketch at `firmware/ESP32_DSIS_AllInOne/ESP32_DSIS_AllInOne.ino`. It connects the ESP32 to an AS608 sensor over UART, an RC522 reader over SPI, and the desktop application to the ESP32 over USB serial.

## Historical and non-authoritative areas

- `python/gui_web/v2_reference/` is a preserved Qt implementation used for comparison and migration reference.
- `archive/legacy-ui/` contains v1 CustomTkinter, older v2 material, prototypes, and investigations. It is not the supported launch path.
- `docs/generated/` contains generated snapshots. Regenerate or verify them before relying on details.
- `docs/Research/` contains concept and study material, not product requirements.
- `docs/Dup/`, old diagnostic reports, and `audit/` preserve history and findings. Their claims are scoped to the snapshot named in each file.

## Documentation ownership

| Topic | Canonical location |
| --- | --- |
| Installation and first run | `docs/UserGuide/installation-guide.md` and `INSTALLATION.md` |
| Operator workflows | `docs/UserGuide/v3-workflows.md` |
| Runtime architecture | `docs/Architecture/v3-system.md` and `docs/Architecture/runtime-contract.md` |
| Database and migrations | `docs/Architecture/database-schema.md` |
| Python/web bridge | `docs/API/README.md` |
| Wiring and firmware | `docs/Hardware/` |
| Testing and source layout | `docs/Development/` |
| Recovery procedures | `docs/Troubleshooting/README.md` |
| Version lineage | `docs/History/README.md` and `docs/History/ui-lineage.md` |

## Known gaps

The repository history establishes 202 commits from `7a300e3` (`Initial commit`, 2026-06-29) through `b311ed4` (`feat: add Karpathy guidelines for coding`, 2026-09-21). Since the previous audit baseline `df0d28b`, the setup wizard gained visible progress and device-status behavior, build targets gained logo/icon support, and the connection modal gained a status side card. Some release tags and early milestones are referenced without a complete release manifest. Board-specific USB bridge details can vary by ESP32 carrier board. Those points must remain qualified until verified from a tag, board schematic, or current source.
