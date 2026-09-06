# Archive

This folder preserves experimental, diagnostic, and legacy UI assets that were separated from the active runtime tree during the project reorganization.

Nothing in this folder is part of the supported DSIS runtime. The active desktop
workflow is the Qt application launched by `run_qt_gui.py`; these files remain for
historical reference and troubleshooting only.

## Contents

- diagnostics/: temporary serial and hardware probe scripts
- legacy-ui/: versioned legacy UI snapshots kept for historical reference

## Legacy UI snapshots

Commit `6b44ca8` added two preserved snapshots under `legacy-ui/`:

- `legacy-ui/v1/` — an earlier PySide6/Qt application tree, including its historical `StudentsPage` enrollment and profile-management flow.
- `legacy-ui/v2/` — an earlier CustomTkinter application tree, including its historical student-list, edit, delete, enrollment, and permission-gated actions.

These snapshots are useful for comparing previous implementations and recovering historical behavior. They are not imported by the active application, are not supported launchers, and should not be used as a substitute for the current code under `python/`.

The current supported desktop workflow remains the Qt application launched by `run_qt_gui.py` or `run_qt_gui.bat`.

The archive is linked from [the documentation index](../docs/INDEX.md). Do not
import archived modules into new application code without verifying their behavior.
