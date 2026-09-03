# Tools Catalog

These scripts support diagnostics, packaging, repository maintenance, and portable-runtime setup. They are not required for normal DSIS use unless a workflow below says otherwise.

| Tool | Purpose | Notes |
| --- | --- | --- |
| `runtime_manager.py` | Manage the optional portable Python runtime and launch workflows | See `docs/Development/PORTABLE_PYTHON.md` |
| `portable_bootstrap.bat` | Install Python requirements for a portable setup | Use only when setting up a portable runtime |
| `build_portable.bat` | Build the historical CustomTkinter portable package | Uses `fingerprint_portable.spec`; not the primary Qt build |
| `fingerprint_portable.spec` | PyInstaller specification for the historical portable workflow | Bundles the legacy application and project assets |
| `verify_gui_startup.py` | Smoke-test the legacy CustomTkinter startup path | Compatibility diagnostic |
| `serial_pipeline_tester.py` | Capture and inspect raw serial/boot output | Requires a connected ESP32; verify the port before use |
| `serial_worker_probe.py` | Probe Qt `SerialWorker` message handling | Requires the application dependencies and serial setup |
| `serial_handler_connect_probe.py` | Probe `SerialHandler` connection behavior | Hardware diagnostic; do not run while another app owns the port |
| `debug_db_connections.py` | Inspect SQLite connection behavior | Use against a development/runtime database only |
| `copilot_forensic_search.py` | Collect repository evidence for local forensic audits | May inspect local VS Code/Copilot storage; treat output as sensitive |
| `archive_unused_python.py` | Identify Python files for archival review | Review results before moving anything |
| `_database_refactor.py` | Historical database refactor helper | Development-only; verify before running |
| `list_files.bat` | Produce a recursive file listing | Inventory helper, not an application launcher; writes `list.txt` at the selected/current directory |

The root `list_files.bat` creates a formatted `tree` snapshot in `list.txt`.
`tools/list_files.bat` is a separate utility that prints a recursive absolute-path
listing to the console. They are not duplicates and both remain available for
manual inventory work. Existing generated snapshots were archived under
`docs/Dup/audit-snapshots/list-output/`.

## Metrics Generator

Run `python audit/generate_metrics.py` from the repository root to regenerate
`audit/source_line_counts.csv`, `docs/CODE_METRICS.csv`, and
`docs/CODE_METRICS.md`. The script counts physical, blank, comment, and code
lines by language and classifies files by component/category.

Current caveats:

- The script contains a machine-specific absolute Windows repository path, so
  it is not portable without editing that value.
- Its exclusion list omits `tests/`, so test source files are currently included
  in the metrics despite tests being excluded from the documentation audit.
- It also scans generated and archived source files unless their paths match the
  script's category rules; the resulting CSV is a snapshot, not a live index.
- It uses Git subprocess calls for history totals but has no shell-specific
  command dependency beyond the availability of Git.

`audit/source_line_counts.csv` is generated output and should be regenerated
after substantial source-tree changes rather than edited manually.

The generator was run successfully from Windows PowerShell on 2026-08-28.
That run measured 181 source files, including 56 files under `tests/`. Execution
on other platforms is not confirmed because the script currently embeds this
machine's Windows absolute repository path.

The active application is launched with the root `run_qt_gui.bat`. The current Qt packaging workflow is documented in [PORTABLE_BUILD.md](../../PORTABLE_BUILD.md); the legacy portable workflow is retained for historical compatibility.

Hardware probes may contain hard-coded COM-port defaults. Confirm the selected port in the script and close Arduino IDE or other serial monitors before running them.

Last verified: 2026-09-03, against commit d68a405
