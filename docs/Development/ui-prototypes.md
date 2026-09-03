# DSIS UI Prototypes

Commit `be7a046` adds isolated Qt interface prototypes for comparing possible layouts and navigation models. They are development previews under `tests/Prototype/`, not alternate production launchers.

## Scope

- Prototypes use mock data or display-only production pages.
- They do not start the live serial worker or database workflow.
- Changes made in a prototype do not change the maintained DSIS application.
- The supported desktop entry point remains `run_qt_gui.bat` and `run_qt_gui.py`.

## Available previews

Run these commands from the repository root:

| Preview | Command | Purpose |
| --- | --- | --- |
| Standalone identification | `python tests/Prototype/run_qt_prototype.py` | Task Manager-inspired identification workspace with mock results |
| Hybrid concept | `python tests/Prototype/run_hybrid_prototype.py` | Identification workspace combined with production-style page navigation |
| Task Manager variant | `python tests/Prototype/run_task_manager_variant.py` | Compact icon navigation and utility-focused comparison layout |
| Original reconstruction | `python tests/Prototype/run_original_ui_display.py` | Display-only reconstruction using the real Qt pages |
| Combined UI | `python tests/Prototype/run_combined_ui.py` | Real Qt pages inside the Task Manager-inspired shell |
| Original-style preview | `python tests/Prototype/original_ui.py` | Standalone comparison with the earlier dark-shell structure |

The previews are useful for visual review and interaction experiments. They are not hardware validation: a successful prototype launch does not prove that serial discovery, fingerprint enrollment, attendance persistence, permissions, or backups work.

## Prototype tests

Run the prototype tests from the repository root:

```powershell
python -m pytest tests/Prototype/tests
```

For end-to-end application behavior, run the main test suite and use the maintained Qt launcher instead of a prototype.

Last reviewed: 2026-09-04, against commit `be7a046`.
