# Archive

This folder preserves experimental, diagnostic, and legacy UI assets that were separated from the active runtime tree during the project reorganization.

Nothing in this folder is part of the supported DSIS runtime. The active desktop
workflow is the Qt application launched by `run_qt_gui.py`; these files remain for
historical reference and troubleshooting only.

## Contents

- diagnostics/: temporary serial and hardware probe scripts
- legacy-ui/: older or duplicate GUI scaffolds kept for historical reference

The archive is linked from [the documentation index](../docs/INDEX.md). Do not
import archived modules into new application code without verifying their behavior.
