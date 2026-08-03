Project documentation consolidation index
=========================================

This file proposes a consolidation of the existing `docs/` folder into a
small set of top-level categories. No files have been moved — the proposed
mapping and suggested move commands are shown below so you can review before
we make any changes.

Proposed categories
-------------------
- Architecture
- Development
- Hardware
- UserGuide
- API
- Research

Proposed file → category mapping
-------------------------------
(Existing file path -> Proposed destination)

Architecture
- architecture.md -> Architecture/architecture.md
- System Architecture.md -> Architecture/system-architecture.md
- Software Flow.md -> Architecture/software-flow.md
- Database Schema.md -> Architecture/database-schema.md

Development
- FILES_OVERVIEW.md -> Development/FILES_OVERVIEW.md
- FILES_DETAILED.md -> Development/FILES_DETAILED.md
- implementation-summary.md -> Development/implementation-summary.md
- DATABASE_INTEGRATION_SUMMARY.md -> Development/database-integration-summary.md
- DATABASE_UPDATES.md -> Development/database-updates.md
- MIGRATION_EXAMPLE.md -> Development/migration-example.md
- LOGGER_USAGE.md -> Development/logger_usage.md
- logging-guide.md -> Development/logging-guide.md
- LOGGING_QUICK_REFERENCE.md -> Development/logging-quick-reference.md
- LOGGING_SUMMARY.md -> Development/logging-summary.md
- Change Log.md -> Development/change-log.md
- POLISH_PHASE_ROADMAP.md -> Development/polish-phase-roadmap.md
- POLISH_PHASE_COMPLETE.md -> Development/polish-phase-complete.md
- fix_report.md -> Development/fix_report.md
- notes.txt -> Development/notes.txt
- todo.md -> Development/todo.md
- structure.txt -> Development/structure.txt
- implementation-summary.md -> Development/implementation-summary.md

UserGuide
- Project Overview.md -> UserGuide/project-overview.md
- Installation Guide.md -> UserGuide/installation-guide.md
- Screenshot*.png -> UserGuide/images/<same-name>
- Testing Results.md -> UserGuide/testing-results.md

Hardware
- Hardware Connections.md -> Hardware/hardware-connections.md
- wiring.md -> Hardware/wiring.md
- IMG*.jpg -> Hardware/images/<same-name>

API
- (Empty for now) — move any API-specific reference docs here (e.g. REST/API design).

Research
- LOGGING_SUMMARY.md (if research-oriented) or move to Development — currently kept in Development
- Any design notes, experiments, and test reports that are research-oriented

Suggested next steps
--------------------
1. Review mapping and confirm or edit categories for specific files.
2. When approved, run the automated move (backup first):

```powershell
# create new folders (already created)
# move markdown docs into new folders
Get-ChildItem docs -Filter "*.md" | Where-Object { $_.Name -in @("architecture.md","System Architecture.md","Software Flow.md","Database Schema.md") } | Move-Item -Destination docs\Architecture
# move screenshots
Get-ChildItem docs -Filter "Screenshot*.png" | Move-Item -Destination docs\UserGuide\images
Get-ChildItem docs -Filter "IMG*.jpg" | Move-Item -Destination docs\Hardware\images
```

3. Update cross-links inside moved markdown files to point to new relative paths.
4. Commit the reorganization in a single commit so history is easy to follow.

If you give the go-ahead, I will (A) move the files as proposed, (B) update internal links
in the moved markdown files, and (C) add `docs/INDEX.md` and a small `docs/README.md`
explaining the consolidation.
