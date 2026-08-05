Documentation Index
===================

This repository's `docs/` folder is now organized into explicit categories.
The previously stray root files have been consolidated, and duplicate
root images have been preserved in `docs/Dup/`.

Top-level sections
------------------

- [Architecture](Architecture/architecture.md)
- [Hardware](Hardware/hardware-connections.md)
- [UserGuide](UserGuide/project-overview.md)
- [Development](Development/change-log.md)
- [Research](Research/)
- [API](API/)
- [Generated Audit](generated/INDEX.md)
- [Duplicates](Dup/README.md)

Current folder purpose
----------------------

- `Architecture/` — system design, data flow, and architecture documentation.
- `Hardware/` — wiring and physical connection documentation.
- `UserGuide/` — installation instructions, usage guidance, and testing results.
- `Development/` — developer notes, change logs, implementation details, and project tracking.
- `Research/` — experimental notes, research findings, and exploratory documentation.
- `API/` — API or interface docs, reserved for future expansion.
- `generated/` — automatically generated audit reports and repository analysis.
- `Dup/` — preserved duplicate files from the legacy docs root.

Duplicate handling
------------------

Duplicate screenshot files that existed both at the `docs/` root and under
`docs/UserGuide/images/` have been moved into `docs/Dup/` to preserve the
original root copies for review. The canonical copies remain in their
category folders.

Notes
-----

- `docs/Dup/` now stores duplicate legacy artifacts so duplicate cleanup is traceable.
- `docs/README.md` explains the current folder organization.
- `docs/INDEX.md` is the primary entry point for docs navigation.
