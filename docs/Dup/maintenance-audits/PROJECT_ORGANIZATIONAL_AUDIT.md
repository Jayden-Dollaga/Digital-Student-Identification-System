# Project Organizational Audit

## Executive Summary

The repository still contains a working fingerprint attendance stack centered on the ESP32 firmware, the Python serial/attendance core, and the Qt desktop UI. The main runtime path is now clearer: the active application is launched from the repository root through the Qt entry point, while the legacy console workflow remains available for compatibility.

The largest organizational issue was the presence of multiple experimental GUI scaffolds, legacy test harnesses, and serial diagnostics sitting beside the active application. Those items were archived into a dedicated archive area so the main project tree is easier to navigate without deleting historical material.

## Current Problems

- The repository mixed active runtime code, experimental GUI redesigns, and diagnostic scripts in the same top-level and Python tree.
- Several files outside the main workflow were easy to mistake for production code.
- The Qt startup path had a thread-exception handler that assumed every thread object exposed `name` and `ident`.
- The project documentation was broader than the actual active structure and needed to reflect the final layout.

## Current Folder Structure

- Root launcher scripts: run_qt_gui.py, run_app.bat, run_qt_gui.bat
- Active Python source: python/
- Firmware sketches: firmware/
- Data and runtime state: data/
- Documentation: docs/
- Generated reports: generated/
- Archived experimental/legacy material: archive/

## Proposed Folder Structure

The project now uses a simplified structure where the live application remains in the main folders and non-production artifacts are archived instead of being mixed into the runtime tree.

- app entry points remain at the repository root
- active Python modules remain under python/
- firmware stays under firmware/
- tests remain under tests/
- documentation remains under docs/
- experimental/duplicate materials are retained under archive/

## File Classification

### Active

- run_qt_gui.py
- python/main.py
- python/gui_qt/
- python/core/
- firmware/ESP32_Fingerprint_AllInOne/
- tests/test_attendance_parsing.py
- tests/test_attendance_processor.py
- tests/test_project_structure.py

### Archived

- archive/diagnostics/
- archive/legacy-ui/

## Dependency Findings

- The Qt UI depends on the Python core modules under python/core/ and the serial handler.
- The firmware and Python host exchange JSON and legacy text messages over serial.
- The active launcher remains the repository root runner and the Qt entry point continues to import correctly through the python/ package path.

## Duplicate Files

- Multiple GUI redesign folders existed under tests/; these were moved into archive/legacy-ui/ to reduce confusion.
- Several temporary serial diagnostics were moved into archive/diagnostics/.

## Legacy Files

- The legacy console workflow in python/main.py remains available for compatibility.
- The older CustomTkinter UI in python/gui/ remains present but is not the primary runtime path.

## Firmware Findings

- The canonical firmware tree remains under firmware/ and continues to be the source for ESP32 behavior.
- Firmware/host protocol compatibility remains intact and was not rewritten as part of this cleanup.

## Serial Protocol Findings

- The Python host still uses the serial handler, attendance processor, and command helpers to exchange data with the ESP32.
- Legacy text compatibility and JSON status parsing remain in place.

## Python Findings

- The core runtime modules under python/core/ remain the architectural backbone.
- The Qt worker and main window remain the active GUI implementation.
- The startup path is now more robust when a worker thread throws an exception before a full thread object is fully initialized.

## GUI Findings

- The Qt GUI remains the recommended desktop UI.
- The user-facing launcher remains run_qt_gui.py and the batch wrapper.

## Threading Findings

- The Qt bootstrap now guards against missing thread metadata when handling uncaught thread exceptions.
- The worker lifecycle remains intact and the app continues to import and run normally.

## Database Findings

- SQLite-backed attendance and student data remain in the active core modules.
- The cleanup did not alter database behavior.

## Testing Findings

- Core regression tests continue to pass after the reorganization.
- The active test suite remains centered on the core parsing and project structure behavior.

## Bugs Fixed

- Fixed a Qt startup robustness issue in the thread exception handler.
- Removed a misleading set of experimental and duplicate GUI/test assets from the active top-level workflow by archiving them.

## Bugs Remaining

- Full hardware validation against a connected ESP32 was not performed in this environment.
- GUI visual regression tests were not run end-to-end because no display-driven interactive session was available here.

## Files Moved

- Root-level serial diagnostic scripts moved to archive/diagnostics/
- tests/gui_qt_redesign and tests/gui_qt_redesign (2) moved to archive/legacy-ui/
- python/testing_area moved to archive/legacy-ui/testing_area

## Files Renamed

- None.

## Files Deleted

- None.

## Compatibility Risks

- External tooling that expected the old experimental paths may need to be updated.
- Some legacy test references may still point to archived folders; those were not rewritten in the active runtime code.

## Validation Results

- Python import check for the Qt entry point: passed
- Core regression tests: 6 passed

## Remaining Technical Debt

- The repository still contains older CustomTkinter and console paths that can be cleaned further later.
- Documentation still has a few references to older experimental directories and should be updated in a later pass.

## Recommended Future Work

- Revisit the archived materials and decide whether any should be removed entirely after the active runtime is fully stable.
- Update the documentation tree to remove stale references to the archived experimental folders.
- Add a small smoke test for the Qt launcher path in headless CI.
