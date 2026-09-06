# v1 — CustomTkinter GUI (archived)

This is the original DSIS desktop interface, built with `customtkinter`.
It was previously mixed into the active `python/` tree alongside v2 (Qt),
which risked the two interfering with each other. It has been moved here
as part of the v3 (HTML/pywebview) migration and is kept for historical
reference only — it is not maintained and should not be run as the active
application.

## Contents
- `python/gui/` — CustomTkinter pages, dialogs, theme, and the legacy
  `gui/legacy/` sub-scaffolds it depended on
- `python/main.py` — the original console/serial entry point tied to this UI
- `python/customtkinter.py` — local shim/vendored module used by this UI
- `python/non_workflow/` — historical utilities that imported directly from
  `gui/app.py` and `gui/theme.py`
- `run_app.bat` — Windows launcher for this UI

## Dependencies
Uses `customtkinter` (see `requirements.txt` at the project root).

## Note
These files import shared backend modules (`core/`, `services/`,
`config.py`, `settings_store.py`) by relative package path assuming they
sit under a `python/` folder at the project root. If you ever want to run
this again, copy `python/gui`, `python/main.py`, `python/customtkinter.py`,
and `python/non_workflow` back into the active `python/` folder alongside
`core/`, `services/`, `config.py`, and `settings_store.py`.
