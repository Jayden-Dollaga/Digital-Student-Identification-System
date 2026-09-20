# DSIS Tools Catalog

These tools support diagnostics, packaging, repository maintenance, and the optional portable runtime. They are not required for normal DSIS attendance use.

## Tool categories

### Runtime and packaging

| Tool | Purpose |
| --- | --- |
| `runtime_manager.py` | Manage optional portable Python runtime workflows |
| `portable_bootstrap.bat` | Install requirements for portable setups |
| `build_portable.bat` | Historical CustomTkinter portable build |
| `fingerprint_portable.spec` | Historical portable PyInstaller specification |

The supported v3 packaged build uses `Build/DSIS_v3.spec`; see [Portable Windows Build](../../PORTABLE_BUILD.md).

### Serial and hardware diagnostics

| Tool | Purpose |
| --- | --- |
| `serial_pipeline_tester.py` | Capture/inspect raw serial and boot output |
| `serial_worker_probe.py` | Probe historical/reference SerialWorker handling |
| `serial_handler_connect_probe.py` | Probe current SerialHandler connection behavior |

Hardware probes should be run only after confirming the intended COM port and closing applications that may own it.

### Database and repository maintenance

| Tool | Purpose |
| --- | --- |
| `debug_db_connections.py` | Inspect SQLite connection behavior |
| `_database_refactor.py` | Historical database refactor helper |
| `archive_unused_python.py` | Identify candidates for archival review |
| `copilot_forensic_search.py` | Collect local forensic evidence for audits; output may be sensitive |
| `tools/list_files.bat` | Print recursive repository file listings |

Historical/refactor scripts should be reviewed before execution. They are not part of the v3 runtime contract.

## Metrics generator

`audit/generate_metrics.py` generates `audit/source_line_counts.csv`, `docs/CODE_METRICS.csv`, and `docs/CODE_METRICS.md`.

These files are snapshots, not authoritative runtime documentation.

Known portability caveats include machine-specific path assumptions and inclusion of files that may be generated, archived, or test-related. Regenerate metrics after substantial source-tree changes rather than editing generated results by hand.

## Safe tool usage

Before running a hardware or database tool:

1. Confirm the target COM port or database.
2. Close DSIS/Arduino Serial Monitor when a tool needs exclusive serial access.
3. Use a development/test database for destructive database operations.
4. Record the tool invocation and resulting changes when troubleshooting.

## Relationship to the application

Tools may diagnose the application, but the supported runtime remains `run_web_gui.py` / `run_web_gui.bat` and the all-in-one ESP32 firmware.

Last reviewed: 2026-09-20.