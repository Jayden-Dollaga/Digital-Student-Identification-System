# DSIS UI Prototypes

The files under `tests/Prototype/` are isolated interface experiments used to evaluate navigation, layout, density, and visual interaction ideas. They are **not alternate production launchers** for the maintained DSIS v3 webview application.

## Why the prototypes exist

DSIS has evolved through multiple UI generations. The prototypes let development work compare ideas without modifying the active v3 interface.

The prototypes are useful for:

- testing navigation concepts;
- comparing information density;
- evaluating sidebar/icon patterns;
- previewing identification workflows;
- testing visual changes before integration.

## Production boundary

The supported production/source launcher is:

```text
run_web_gui.py
run_web_gui.bat
```

The active interface is HTML/CSS/JavaScript rendered by pywebview.

Historical interfaces are retained under `archive/legacy-ui/`.

A prototype launch does **not** prove:

- serial discovery;
- ESP32/AS608 communication;
- fingerprint enrollment;
- attendance persistence;
- permissions;
- database backup/restore;
- v3 API behavior.

## Available previews

| Preview | Command | Scope |
| --- | --- | --- |
| Standalone identification | `python tests/Prototype/run_qt_prototype.py` | Mock identification workspace |
| Hybrid concept | `python tests/Prototype/run_hybrid_prototype.py` | Identification + page-navigation concept |
| Task Manager variant | `python tests/Prototype/run_task_manager_variant.py` | Compact icon navigation concept |
| Original reconstruction | `python tests/Prototype/run_original_ui_display.py` | Display-only reconstruction using Qt pages |
| Combined UI | `python tests/Prototype/run_combined_ui.py` | Qt pages inside experimental shell |
| Original-style preview | `python tests/Prototype/original_ui.py` | Comparison with the earlier dark-shell structure |

## Data and hardware isolation

Prototypes use mock, fixture, or display-only data. They should not be used as a substitute for the live SQLite database or serial hardware.

A prototype should not write production attendance records, modify real fingerprints, or perform destructive device operations.

## Validation

Run a prototype from the repository root only when reviewing interface behavior:

```powershell
python tests/Prototype/run_qt_prototype.py
```

For application correctness, use the maintained v3 launcher and the normal test suite.

## Integration rule

A prototype becomes part of the active application only after its behavior is deliberately integrated into `python/gui_web/web/` and/or the supported Python backend, with corresponding tests and documentation updates.

Last reviewed: 2026-09-20.
