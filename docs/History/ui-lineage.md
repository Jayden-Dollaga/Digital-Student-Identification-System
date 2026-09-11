# DSIS UI Lineage

## v1: CustomTkinter

The original desktop interface used CustomTkinter and lived in the earlier Python GUI tree. It provided the first operational student, attendance, settings, and serial workflows. The preserved snapshot is `archive/legacy-ui/v1/`.

## v2: PySide6/Qt

The second-generation interface introduced PySide6, page-based navigation, background serial workers, richer connection handling, reports, settings, enrollment dialogs, and theme stylesheets. Its historical launchers and source are preserved in `archive/legacy-ui/v2/`. The reference copy under `python/gui_web/v2_reference/` is used to compare workflow and protocol behavior with v3.

## v3: HTML/pywebview

The maintained interface is v3. `run_web_gui.py` opens a native pywebview window around `python/gui_web/web/index.html`. The browser-side JavaScript calls `window.pywebview.api`; Python sends asynchronous events through `window.dsisEvent`.

V3 keeps the backend responsibilities developed during v2 but changes the presentation boundary:

- HTML/CSS/JavaScript replace Qt widgets.
- `python/gui_web/api.py` replaces Qt signal/slot glue for frontend operations.
- Serial and database logic remains in `python/core`.
- The v2 implementation is reference-only and is not imported at runtime.

## Version and release notes

The repository has `v0.1.0` and `v2.5.0` tags, but v3 is still current main-branch work rather than a published v3 release. Do not infer a v3 release version from the current branch until a release tag and release notes are created.

## Historical documentation policy

Files under `archive/`, `docs/generated/`, and historical investigation folders preserve earlier states. They may mention removed launchers, old UI frameworks, or previous test counts. Use the active README, UserGuide, Architecture, Hardware, Development, and Troubleshooting sections for current behavior.

Last reviewed: 2026-09-11, against commit `aa457e0`.
