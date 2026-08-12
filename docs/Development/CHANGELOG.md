## Unreleased

### Fixes

- 2026-08-12 — Fix: Native Qt shutdown crash (Windows) — Implemented defensive cleanup in
  `MainWindow.closeEvent` to disconnect `SerialWorker` signals and ensure the worker
  thread is stopped and waited on during UI teardown. Validated by repeated test runs
  (see technical note). Classified: FIXED — VERIFIED BY REPEATED TEST RUNS.
