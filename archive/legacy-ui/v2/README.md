# v2 — PySide6 Qt GUI (archived)

This is the second-generation DSIS desktop interface, built with PySide6/Qt.
It reached live-testing readiness and was the active runtime UI before the
v3 (HTML/pywebview) migration. It was previously mixed into the active
`python/` tree alongside v1 (CustomTkinter), which risked the two
interfering with each other. It has been moved here for historical
reference and as a fallback — it is not the actively developed UI going
forward, but it is left runnable if v3 needs a working comparison point.

## Contents
- `python/gui_qt/` — the full Qt application: `main_qt.py`, `main_window.py`,
  `pages/`, `widgets/`, `workers/`, and both QSS themes
- `run_qt_gui.py` / `run_qt_gui.bat` — entry point and Windows launcher

## Dependencies
Uses `PySide6` (see `requirements.txt` at the project root).

## Note
These files import shared backend modules (`core/`, `services/`,
`config.py`, `settings_store.py`) by relative package path assuming they
sit under a `python/` folder at the project root. To run this again, copy
`python/gui_qt` back into the active `python/` folder alongside `core/`,
`services/`, `config.py`, and `settings_store.py`, and put `run_qt_gui.py`
/ `run_qt_gui.bat` back at the project root.
