Duplicate documentation artifacts
===============================

This folder contains legacy duplicates that were originally present in the `docs/` root.
The files here are preserved for review, but the canonical versions are kept in their category folders.

Currently preserved duplicates:

- `duplicate-notes/notes.txt` — exact duplicate of the former `docs/Development/notes.txt`, archived on 2026-08-28
- `duplicate-screenshots/*.png` — 59 MD5-confirmed duplicates of screenshots in `docs/UserGuide/images/`, organized here on 2026-08-28
- `audit-snapshots/*.txt` — point-in-time Git audit outputs moved from the `docs/` root on 2026-08-28
- `audit-snapshots/list-output/root-list.txt` and `python-list.txt` — stale committed directory-list snapshots archived on 2026-08-28; future `list.txt` output is ignored
- `superseded-changelogs/CHANGELOG.md` — one-entry changelog merged into `docs/Development/change-log.md` on 2026-08-28
- `historical-investigations/` — resolved enrollment final summary and GUI flicker fix report archived on 2026-08-28
- `maintenance-audits/PROJECT_ORGANIZATIONAL_AUDIT.md` — superseded organizational audit archived on 2026-08-28

The unresolved enrollment reports remain in the docs root for review:

- `ENROLLMENT_REGRESSION_DIAGNOSTIC.md`
- `ROOT_CAUSE_ANALYSIS.md`

The security reports remain in place because their own remediation report lists deferred findings.

Keep this folder only while reviewing or migrating duplicates. Once the duplicate files have been confirmed as safe to discard, they can be removed.
