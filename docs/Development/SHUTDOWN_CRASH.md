Title: Native Qt Shutdown Crash (Windows) — Investigation & Fix
Date: 2026-08-12

Summary
-------

Observed a native Windows access violation (exit code -1073741819 / 0xC0000005)
occurring during process teardown after running pytest that exercised the
PySide6-based Qt UI. The failure happened after pytest reported passing tests
and correlated with certain combinations of Qt-heavy tests running in the same
process.

Symptoms
--------

- Native crash on process exit with code -1073741819 (0xC0000005).
- Occurred intermittently depending on the set/ordering of Qt tests in a single
  pytest execution.
- No Python-level traceback was available (native crash during Qt teardown).

Suspected cause
---------------

Likely a lifetime / ordering issue between `QThread` (`SerialWorker`) and
Qt `QObject`-based UI elements. Signal emissions or thread activity may have
occurred while widgets were being destroyed during application shutdown,
leading to a use-after-free in native Qt code (observed only on Windows in
this environment).

Implemented change
------------------

- Added defensive cleanup in `MainWindow.closeEvent` to:
  - Explicitly disconnect `SerialWorker` signals bound to UI slots/pages.
  - Call `SerialWorker.stop()` to set the run flag and request interruption.
  - Call `quit()` and `wait(2000)` on the `SerialWorker` thread to allow
    orderly termination.

- The change is localized to `MainWindow.closeEvent` and did not alter overall
  architecture, serial protocol, or other components.

Validation performed
--------------------

- Targeted Qt tests: executed the previously-failing combinations (e.g.
  `tests/test_qt_shell.py` + `tests/test_qt_settings_logs.py`) — passed.
- Full test suite: ran `python -m pytest -q` multiple times — reported
  "56 passed, 2 skipped" consistently.
- After the fix, the original native crash (-1073741819) did not reproduce
  across several full-suite runs that previously triggered it.

Classification
--------------

FIXED — VERIFIED BY REPEATED TEST RUNS

Note: no deterministic regression test currently reproduces the original
native crash; the fix is validated by repeated runs but a reproducer is
still needed to prove resolution under all permutations.

Next recommended steps (documentation only)
-----------------------------------------

- Create a reliable, deterministic reproducer test that triggers the native
  crash (if possible) so the fix can be regression-tested automatically.
- Consider instrumenting Windows native crash dumps during CI runs to capture
  a native stack trace if the crash recurs.

Files modified
--------------

- `python/gui_qt/main_window.py` — defensive disconnect and orderly thread
  shutdown in `closeEvent`.
