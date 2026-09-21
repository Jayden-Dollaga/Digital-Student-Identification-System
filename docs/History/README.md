# Project History

DSIS has three meaningful UI generations. The source history contains many incremental commits, so this summary describes architecture boundaries rather than claiming that every feature landed in one release.

## v1: CustomTkinter

The original desktop interface combined Python GUI code, serial communication, SQLite operations, and student/attendance workflows. Preserved sources live under `archive/legacy-ui/v1/`. They explain early behavior but are not the current launch path.

## v2: Qt/PySide6

The Qt generation separated pages, workers, serial handling, database access, attendance processing, permissions, backups, and reports more clearly. The preserved implementation is under `python/gui_web/v2_reference/` and related archive paths. It remains useful for parity comparison and historical debugging, but v2 widgets and signal/slot paths are not imported by the v3 launcher.

## v3: HTML and pywebview

The current UI keeps the shared Python core and replaces Qt presentation and signal/slot glue with HTML/CSS/JavaScript. `main_web.py` creates the pywebview window, `api.py` exposes the Python bridge, and `web/app.js` renders state and sends user actions. Backend events are pushed to the frontend through the pywebview event bridge.

## Recent audited history

The previous audit baseline was `df0d28b` on 2026-09-20. The current HEAD is
`b311ed4` on 2026-09-21. Commits since that baseline include:

- `80939ff`: setup wizard progress tracking and device connection status in the v3 web UI.
- `3505b10`: logo/icon support across application versions and build specifications.
- `82a2ac0`: a connection modal side card for live status detail.
- `b311ed4`: repository coding-guideline instructions; this changes contributor process, not runtime behavior.

These changes are presentation and development-process updates. They do not
replace the Python bridge, SQLite schema, firmware protocol, or attendance
processor contract described by the architecture guides.

## History limits

The checked-out repository contains 202 commits from `7a300e3` through
`b311ed4` at the time of this audit. The curated changelog and audit files
group some changes and omit details for some tags, so exact release boundaries
must be read from Git tags and commit contents rather than inferred from
document titles. Historical reports remain under their original paths to
preserve provenance.
