# DSIS Documentation Architecture & Maintenance Guide

> **Purpose:** Explain how the entire `docs/` tree is organized, which material is authoritative, and where a reader should go for a particular kind of information.

The DSIS repository contains more than user instructions. It contains architecture references, hardware documentation, development notes, troubleshooting records, historical investigations, generated audits, and concept/research material. This document keeps those purposes separate so the repository can remain information-rich without becoming misleading.

## Documentation principles

DSIS documentation follows four rules:

1. **Current implementation comes first.** Documentation should describe the maintained v3 application unless explicitly marked otherwise.
2. **Historical material is preserved, not silently treated as current.** Old investigations and UI implementations remain useful for provenance and debugging.
3. **Generated reports are evidence, not contracts.** A generated audit describes the repository at the time it was produced.
4. **Research is separate from technical product documentation.** Concept papers may explain why or how DSIS was conceived, but they do not define runtime behavior.

When documents conflict, use this priority:

```text
Current source code + tests
          │
          ▼
Current v3 documentation
          │
          ▼
Release / deployment documentation
          │
          ▼
Historical investigations
          │
          ▼
Generated snapshots / audits
```

## Documentation tree

```text
docs/
│
├── README.md                         Documentation homepage
├── INDEX.md                          Detailed navigation index
├── Documentation-Overhaul.md         This maintenance guide
├── Documentation-Inventory.md        File classification / inventory
│
├── Architecture/                     HOW THE SYSTEM WORKS
│   ├── v3-system.md                  Current runtime architecture
│   ├── system-architecture.md        Layered architecture
│   ├── software-flow.md              Runtime/data flow
│   └── database-schema.md            SQLite structure and rules
│
├── Hardware/                         PHYSICAL DEVICE
│   ├── hardware-connections.md       Hardware architecture + wiring
│   ├── wiring.md                     Pin and power reference
│   └── firmware-variants.md          Firmware lineage and variants
│
├── UserGuide/                        HOW TO INSTALL AND USE DSIS
│   ├── project-overview.md           Product/system overview
│   ├── installation-guide.md         Installation and setup
│   ├── v3-workflows.md               Daily workflows
│   └── testing-results.md            Validation results
│
├── Troubleshooting/                  WHEN SOMETHING BREAKS
│   └── README.md                     Current quick recovery guide
│
├── Development/                     HOW TO DEVELOP AND MAINTAIN DSIS
│   ├── documentation-map.md          Documentation rules
│   ├── FILES_OVERVIEW.md             Source-tree overview
│   ├── FILES_DETAILED.md             Python/module guide
│   ├── database-updates.md           Database maintenance
│   ├── implementation-summary.md     Implementation state
│   ├── logging-guide.md              Logging
│   ├── runtime-data.md               Runtime-data policy
│   ├── tools-catalog.md              Developer tools
│   ├── ui-prototypes.md              Non-production prototypes
│   └── ...                           Historical development notes
│
├── History/                          VERSION / UI EVOLUTION
│   └── ui-lineage.md                 v1 → v2 → v3 history
│
├── generated/                        AUTOMATED SNAPSHOTS
│
├── Dup/                              PRESERVED DUPLICATES / SUPERSEDED MATERIAL
│
├── Research/                         CONCEPT / SCHOOL RESEARCH
│
└── _inbox/                           DOCUMENTATION ASSET INBOX
```

## Current v3 source of truth

The maintained application is the v3 HTML/JavaScript interface hosted in pywebview.

| Layer | Source |
| --- | --- |
| Launcher | `run_web_gui.py`, `run_web_gui.bat` |
| Native shell | `python/gui_web/main_web.py` |
| Python ↔ JavaScript bridge | `python/gui_web/api.py` |
| Frontend | `python/gui_web/web/` |
| Core backend | `python/core/` |
| Compatibility services | `python/services/` |
| Database | SQLite under `data/` |
| Settings | Local JSON settings |
| Logs | `data/logs/` |
| Firmware | `firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino` |
| Packaging | `Build/DSIS_v3.spec` |

The v3 runtime uses this primary communication path:

```text
HTML/CSS/JavaScript
        │
        │ window.pywebview.api
        ▼
Python API bridge
        │
        ├── device discovery
        ├── serial handler
        ├── attendance processor
        ├── permissions/authentication
        ├── database
        ├── backups/reports
        └── logging
        │
        │ USB serial 115200
        ▼
ESP32
        │
        │ UART 57600
        ▼
AS608
```

## What the documentation covers

### Architecture

The architecture documentation should answer:

- What components exist?
- Which component owns each responsibility?
- How does JavaScript call Python?
- How does Python discover and validate the ESP32?
- How are serial events parsed?
- How does enrollment become a student record?
- How does a scan become an attendance event?
- How are permissions enforced?
- How does the database relate to backups and reports?

Start with [v3 System Architecture](Architecture/v3-system.md).

### Hardware

The hardware documentation should answer:

- Which ESP32 target is verified?
- Which AS608 connections are required?
- Which GPIO pins are used?
- Which baud rate belongs to each serial link?
- What power assumptions are safe?
- How can a hardware fault be separated from a software fault?

Start with [Hardware Reference](Hardware/hardware-connections.md).

### User operation

The user documentation should answer:

- How do I upload firmware?
- How do I launch DSIS?
- How do I connect the device?
- How do I enroll a student?
- How does scanning work?
- How are attendance evaluations calculated?
- How do I export or back up data?
- What should I do when the device disconnects?

Start with [Installation Guide](UserGuide/installation-guide.md) and [v3 Workflows](UserGuide/v3-workflows.md).

### Development

Developer documentation should explain source ownership, runtime data, database behavior, logging, packaging, tests, prototypes, and maintenance conventions. It should link directly to source files where a reader needs to inspect implementation details.

## Research is intentionally separate

`docs/Research/` contains **concept papers and research-oriented material**. It is not part of the operational or technical source-of-truth chain.

Research documents can explain:

- the original problem being addressed;
- project motivation;
- proposed concepts;
- research methodology or school requirements;
- future ideas that have not been implemented.

They should **not** be used to determine whether a feature exists in the current application.

This separation is intentional: someone installing DSIS should not need to read the concept paper, while someone evaluating the project's research background should still be able to find it.

## Historical material

Historical documents are valuable because DSIS has evolved through multiple UI generations:

```text
v1 ── CustomTkinter
 │
 ▼
v2 ── PySide6 / Qt
 │
 ▼
v3 ── HTML/CSS/JavaScript + pywebview
```

The current runtime is v3. Historical v1/v2 implementations are retained for provenance and comparison under `archive/legacy-ui/` and related reference paths.

Historical documents should therefore be labeled with their scope rather than deleted merely because they are old.

## Generated material

`docs/generated/` contains reports produced from a particular repository state. Examples include architecture audits, database inventories, GUI reports, firmware inventories, testing summaries, and repository forensic reports.

Generated documents are useful for:

- auditing;
- comparing repository states;
- reviewing historical implementation details;
- identifying documentation gaps.

They are not suitable as primary installation instructions because their paths, counts, test results, or implementation descriptions can become stale.

## Documentation quality standard

A high-quality DSIS document should contain, where applicable:

- **Purpose** — why the document exists.
- **Scope** — current v3, historical version, hardware revision, or generated snapshot.
- **Audience** — user, administrator, developer, reviewer, or researcher.
- **Prerequisites** — hardware/software assumptions.
- **Procedure** — ordered steps for tasks.
- **Expected result** — what success looks like.
- **Failure modes** — common symptoms and likely causes.
- **Source links** — direct paths to relevant implementation files.
- **Cross-links** — related documentation instead of duplicated explanations.
- **Last reviewed date** — so stale material can be identified.

## Maintenance workflow

When a feature changes:

1. Update the implementation and tests.
2. Update the relevant architecture document if system behavior changed.
3. Update the user workflow if the operator experience changed.
4. Update hardware/firmware documentation if device behavior changed.
5. Update troubleshooting guidance if the failure mode or recovery procedure changed.
6. Update the documentation inventory when a document changes classification.
7. Regenerate generated reports only when their generator and source state are known.

## Known documentation boundaries

Some documents intentionally remain outside the current source-of-truth path:

- `Research/` — concept/research material.
- `generated/` — generated snapshots.
- `Dup/` — preserved duplicates/superseded documents.
- historical investigations — provenance and debugging context.
- archived UI documentation — v1/v2 reference.

Keeping these materials is useful. Presenting them as current implementation documentation is not.

Last reviewed: 2026-09-20.
