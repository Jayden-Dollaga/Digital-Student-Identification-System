Project documentation repository
===============================

This `docs/` folder is organized by documentation category and purpose.
It is intentionally separated into:

- `Architecture/` – system architecture, data flow, and database design.
- `Hardware/` – wiring, hardware connections, and physical component references.
- `UserGuide/` – installation, user instructions, and manual testing results.
- `Development/` – developer notes, change logs, implementation details, and project tracking.
- `API/` – API or interface documentation (currently empty, reserved for future references).
- `Research/` – design notes, research findings, and exploratory documentation.
- `generated/` – audit reports and automatically generated documentation artifacts.
- `Dup/` – preserved duplicate files from the legacy docs root.

Duplicate artifacts are preserved in `docs/Dup/` rather than being removed silently.
This ensures original source copies remain available in their intended folders while
root duplicates are grouped for review.

If you add new documentation files, place them in the folder whose name best describes
their domain, and update `docs/INDEX.md` if you add a new top-level category.
