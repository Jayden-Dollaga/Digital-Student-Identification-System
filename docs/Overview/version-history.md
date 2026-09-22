# Version History and Product Evolution

DSIS has passed through multiple implementation generations. The codebase retains these implementations for historical and debugging purposes, but only the current v3 path is treated as the supported operational product.

## v1: CustomTkinter-era interface

- Location: `archive/legacy-ui/v1`
- Toolkit: CustomTkinter
- Purpose: early desktop UI prototype and iteration for the school attendance workflow
- Status: historical, archived

## v2: Qt-era interface

- Location: `archive/legacy-ui/v2` and relevant `python/gui_qt` code
- Toolkit: Qt/PySide-style desktop UI
- Purpose: richer desktop app with more mature settings and attendance management
- Status: historical, archived

## v3: current webview-based interface

- Location: `python/gui_web/`
- Toolkit: pywebview + HTML/CSS/JS
- Purpose: current supported desktop interface for DSIS
- Status: active product

## Why the history matters

The repository intentionally keeps the older UI implementations because they preserve:

- implementation lineage,
- bug-fix context,
- proof for regressions,
- code that was used to compare or port older logic into the v3 path.

The current docs and the active runtime should not be based on those older implementations unless the behavior is still present in the v3 code and tested in the live repo.
