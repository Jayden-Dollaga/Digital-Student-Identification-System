# DSIS Full Project Architecture Tree

> **Generated from the repository's `main` tree.**
>
> This document is the literal project tree plus a source-symbol tree. It is intentionally more detailed than the high-level architecture documents.
>
> **How to read it:** every repository file is listed in the first tree. Source files are expanded later into classes/functions so the architecture can be followed from folder → file → symbol.
>
> Historical/archive files are shown as files because they are part of the repository; they are not presented as current runtime code.

## 1. Complete repository file tree

```text
Digital-Student-Identification-System/
  ├── .github
  │   ├── instructions
  │   │   └── SKILL.instructions.md
  │   └── workflows
  │       └── tests.yml
  ├── Build
  │   ├── DSIS_v1.spec
  │   ├── DSIS_v2.spec
  │   └── DSIS_v3.spec
  ├── archive
  │   ├── diagnostics
  │   │   ├── discovery_handshake_probe.py
  │   │   ├── serial_monitor_test.py
  │   │   ├── serial_pipeline_tester.py
  │   │   ├── temp_serial_port_info.py
  │   │   ├── tmp_serial_dtr_test.py
  │   │   ├── tmp_serial_handler_probe.py
  │   │   └── tmp_serial_probe.py
  │   ├── legacy-ui
  │   │   ├── gui_qt_redesign
  │   │   │   ├── gui_qt
  │   │   │   │   ├── pages
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── attendance_page.py
  │   │   │   │   │   ├── dashboard_page.py
  │   │   │   │   │   ├── logs_page.py
  │   │   │   │   │   ├── reports_page.py
  │   │   │   │   │   ├── settings_page.py
  │   │   │   │   │   └── students_page.py
  │   │   │   │   ├── widgets
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── sidebar.py
  │   │   │   │   │   └── stat_card.py
  │   │   │   │   ├── workers
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   └── serial_worker.py
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── main_qt.py
  │   │   │   │   ├── main_window.py
  │   │   │   │   └── theme.qss
  │   │   │   └── README.md
  │   │   ├── gui_qt_redesign_2
  │   │   │   ├── gui_qt
  │   │   │   │   ├── pages
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── attendance_page.py
  │   │   │   │   │   ├── dashboard_page.py
  │   │   │   │   │   ├── logs_page.py
  │   │   │   │   │   ├── reports_page.py
  │   │   │   │   │   ├── settings_page.py
  │   │   │   │   │   └── students_page.py
  │   │   │   │   ├── widgets
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── sidebar.py
  │   │   │   │   │   └── stat_card.py
  │   │   │   │   ├── workers
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   └── serial_worker.py
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── main_qt.py
  │   │   │   │   ├── main_window.py
  │   │   │   │   └── theme.qss
  │   │   │   └── README.md
  │   │   ├── testing_area
  │   │   │   ├── core
  │   │   │   │   └── database_addition_snippet.py
  │   │   │   ├── gui
  │   │   │   │   └── legacy
  │   │   │   │       ├── app_test.py
  │   │   │   │       ├── app_test1.py
  │   │   │   │       ├── bfeas_app.py
  │   │   │   │       ├── bfeas_app2.py
  │   │   │   │       └── reports_table_page.py
  │   │   │   ├── services
  │   │   │   │   ├── backup.py
  │   │   │   │   └── excel_export.py
  │   │   │   └── README.txt
  │   │   ├── v1
  │   │   │   ├── python
  │   │   │   │   ├── core
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── attendance.py
  │   │   │   │   │   ├── commands.py
  │   │   │   │   │   ├── database.py
  │   │   │   │   │   ├── logger.py
  │   │   │   │   │   ├── serial_handler.py
  │   │   │   │   │   └── utils.py
  │   │   │   │   ├── gui
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── app.py
  │   │   │   │   │   ├── attendance_page.py
  │   │   │   │   │   ├── dashboard.py
  │   │   │   │   │   ├── dialogs.py
  │   │   │   │   │   ├── log_page.py
  │   │   │   │   │   ├── main_window.py
  │   │   │   │   │   ├── reports_page.py
  │   │   │   │   │   ├── settings_dialog.py
  │   │   │   │   │   ├── settings_page.py
  │   │   │   │   │   ├── sidebar.py
  │   │   │   │   │   ├── statistics_page.py
  │   │   │   │   │   ├── students_page.py
  │   │   │   │   │   ├── theme.py
  │   │   │   │   │   └── widgets.py
  │   │   │   │   ├── services
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── attendance_service.py
  │   │   │   │   │   ├── backup.py
  │   │   │   │   │   ├── excel_export.py
  │   │   │   │   │   └── student_service.py
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── config.py
  │   │   │   │   ├── fix_emoji.py
  │   │   │   │   ├── main.py
  │   │   │   │   └── settings_store.py
  │   │   │   ├── README.md
  │   │   │   └── run_app.bat
  │   │   └── v2
  │   │       ├── python
  │   │       │   ├── core
  │   │       │   │   ├── __init__.py
  │   │       │   │   ├── attendance.py
  │   │       │   │   ├── commands.py
  │   │       │   │   ├── database.py
  │   │       │   │   ├── device_discovery.py
  │   │       │   │   ├── firmware_helper.py
  │   │       │   │   ├── logger.py
  │   │       │   │   ├── permissions.py
  │   │       │   │   ├── serial_handler.py
  │   │       │   │   └── utils.py
  │   │       │   ├── gui
  │   │       │   │   ├── legacy
  │   │       │   │   │   ├── bfeas_app2.py
  │   │       │   │   │   └── reports_table_page.py
  │   │       │   │   ├── __init__.py
  │   │       │   │   ├── app.py
  │   │       │   │   ├── attendance_page.py
  │   │       │   │   ├── dashboard.py
  │   │       │   │   ├── dialogs.py
  │   │       │   │   ├── layout_utils.py
  │   │       │   │   ├── log_page.py
  │   │       │   │   ├── perf_profiler.py
  │   │       │   │   ├── reports_page.py
  │   │       │   │   ├── serial_troubleshooting.py
  │   │       │   │   ├── settings_dialog.py
  │   │       │   │   ├── settings_page.py
  │   │       │   │   ├── sidebar.py
  │   │       │   │   ├── statistics_page.py
  │   │       │   │   ├── students_page.py
  │   │       │   │   └── theme.py
  │   │       │   ├── gui_qt
  │   │       │   │   ├── pages
  │   │       │   │   │   ├── __init__.py
  │   │       │   │   │   ├── attendance_page.py
  │   │       │   │   │   ├── dashboard_page.py
  │   │       │   │   │   ├── logs_page.py
  │   │       │   │   │   ├── reports_page.py
  │   │       │   │   │   ├── settings_page.py
  │   │       │   │   │   └── students_page.py
  │   │       │   │   ├── widgets
  │   │       │   │   │   ├── __init__.py
  │   │       │   │   │   ├── sidebar.py
  │   │       │   │   │   └── stat_card.py
  │   │       │   │   ├── workers
  │   │       │   │   │   ├── __init__.py
  │   │       │   │   │   ├── connection_worker.py
  │   │       │   │   │   └── serial_worker.py
  │   │       │   │   ├── __init__.py
  │   │       │   │   ├── main_qt.py
  │   │       │   │   ├── main_window.py
  │   │       │   │   ├── theme.qss
  │   │       │   │   └── theme_light.qss
  │   │       │   ├── non_workflow
  │   │       │   │   ├── fix_emoji.py
  │   │       │   │   ├── main_window.py
  │   │       │   │   ├── serial.py
  │   │       │   │   └── widgets.py
  │   │       │   ├── services
  │   │       │   │   ├── __init__.py
  │   │       │   │   ├── attendance_service.py
  │   │       │   │   └── student_service.py
  │   │       │   ├── __init__.py
  │   │       │   ├── config.py
  │   │       │   ├── customtkinter.py
  │   │       │   ├── main.py
  │   │       │   └── settings_store.py
  │   │       ├── README.md
  │   │       ├── run_qt_gui.bat
  │   │       └── run_qt_gui.py
  │   └── README.md
  ├── assets
  │   └── icon
  │       ├── DSIS_LOGO.ico
  │       ├── DSIS_LOGO.png
  │       └── dsis-logo.html
  ├── audit
  │   ├── FORENSIC_AUDIT.md
  │   ├── generate_metrics.py
  │   └── source_line_counts.csv
  ├── docs
  │   ├── API
  │   │   └── README.md
  │   ├── Architecture
  │   │   ├── README.md
  │   │   ├── architecture.md
  │   │   ├── complete-system-architecture.md
  │   │   ├── data-and-settings.md
  │   │   ├── database-schema.md
  │   │   ├── pywebview-bridge-api-reference.md
  │   │   ├── pywebview-bridge.md
  │   │   ├── runtime-contract.md
  │   │   ├── software-flow.md
  │   │   ├── system-architecture.md
  │   │   ├── v3-system-architecture-detail.md
  │   │   ├── v3-system-architecture.md
  │   │   └── v3-system.md
  │   ├── Development
  │   │   ├── ESP32_Fingerprint_AllInOne_firmware_explanation.md
  │   │   ├── FILES_DETAILED.md
  │   │   ├── FILES_OVERVIEW.md
  │   │   ├── PORTABLE_PYTHON.md
  │   │   ├── README.md
  │   │   ├── SHUTDOWN_CRASH.md
  │   │   ├── change-log.md
  │   │   ├── database-integration-summary.md
  │   │   ├── database-updates.md
  │   │   ├── documentation-authority.md
  │   │   ├── documentation-manifest.md
  │   │   ├── documentation-map.md
  │   │   ├── implementation-summary.md
  │   │   ├── logger_usage.md
  │   │   ├── logging-guide.md
  │   │   ├── logging-quick-reference.md
  │   │   ├── logging-summary.md
  │   │   ├── logging.md
  │   │   ├── migration-example.md
  │   │   ├── polish-phase-complete.md
  │   │   ├── polish-phase-roadmap.md
  │   │   ├── release-and-portable-build.md
  │   │   ├── runtime-data.md
  │   │   ├── setup.md
  │   │   ├── structure.txt
  │   │   ├── testing.md
  │   │   ├── todo.md
  │   │   ├── tools-catalog.md
  │   │   └── ui-prototypes.md
  │   ├── Dup
  │   │   └── README.md
  │   ├── Hardware
  │   │   ├── images
  │   │   │   ├── IMG20260630233940.jpg
  │   │   │   ├── IMG20260630233946.jpg
  │   │   │   ├── IMG20260630233949.jpg
  │   │   │   ├── IMG20260630235111.jpg
  │   │   │   ├── IMG20260630235113.jpg
  │   │   │   ├── IMG20260630235115.jpg
  │   │   │   ├── IMG20260630235122.jpg
  │   │   │   ├── IMG20260630235124.jpg
  │   │   │   ├── IMG20260630235318.jpg
  │   │   │   ├── IMG20260701000304.jpg
  │   │   │   ├── IMG20260701000309.jpg
  │   │   │   ├── IMG20260701000315.jpg
  │   │   │   ├── IMG20260701000319.jpg
  │   │   │   ├── IMG20260701000326.jpg
  │   │   │   ├── IMG20260701000328.jpg
  │   │   │   ├── IMG20260701010721.jpg
  │   │   │   ├── IMG20260701010726.jpg
  │   │   │   └── IMG20260701010735.jpg
  │   │   ├── README.md
  │   │   ├── drivers-and-ports.md
  │   │   ├── firmware-variants.md
  │   │   ├── firmware.md
  │   │   ├── hardware-connections.md
  │   │   ├── serial-protocol.md
  │   │   └── wiring.md
  │   ├── History
  │   │   ├── README.md
  │   │   └── ui-lineage.md
  │   ├── Overview
  │   │   ├── project-overview.md
  │   │   └── version-history.md
  │   ├── Research
  │   │   ├── DSIS_CONCEPT_PAPER.md
  │   │   └── DSIS_CONCEPT_PAPER_SOURCE_NOTES.md
  │   ├── Security
  │   │   └── security-model.md
  │   ├── Troubleshooting
  │   │   ├── README.md
  │   │   ├── database.md
  │   │   ├── desktop.md
  │   │   └── serial-and-device.md
  │   ├── UserGuide
  │   │   ├── images
  │   │   │   ├── 151746.png
  │   │   │   ├── 151826.png
  │   │   │   ├── Screenshot 2026-06-27 182256.png
  │   │   │   ├── Screenshot 2026-06-29 232644.png
  │   │   │   ├── Screenshot 2026-06-29 233641.png
  │   │   │   ├── Screenshot 2026-06-30 115359.png
  │   │   │   ├── Screenshot 2026-06-30 115404.png
  │   │   │   ├── Screenshot 2026-06-30 190312.png
  │   │   │   ├── Screenshot 2026-06-30 193423.png
  │   │   │   ├── Screenshot 2026-06-30 193928.png
  │   │   │   ├── Screenshot 2026-06-30 194343.png
  │   │   │   ├── Screenshot 2026-06-30 194530.png
  │   │   │   ├── Screenshot 2026-06-30 195210.png
  │   │   │   ├── Screenshot 2026-06-30 200710.png
  │   │   │   ├── Screenshot 2026-06-30 201634.png
  │   │   │   ├── Screenshot 2026-06-30 204935.png
  │   │   │   ├── Screenshot 2026-06-30 205811.png
  │   │   │   ├── Screenshot 2026-06-30 205826.png
  │   │   │   ├── Screenshot 2026-06-30 212105.png
  │   │   │   ├── Screenshot 2026-06-30 213207.png
  │   │   │   ├── Screenshot 2026-06-30 214250.png
  │   │   │   ├── Screenshot 2026-06-30 223351.png
  │   │   │   ├── Screenshot 2026-06-30 230553.png
  │   │   │   ├── Screenshot 2026-06-30 230614.png
  │   │   │   ├── Screenshot 2026-06-30 231636.png
  │   │   │   ├── Screenshot 2026-06-30 234700.png
  │   │   │   ├── Screenshot 2026-07-01 215932.png
  │   │   │   ├── Screenshot 2026-07-01 220522.png
  │   │   │   ├── Screenshot 2026-07-01 220725.png
  │   │   │   ├── Screenshot 2026-07-01 222527.png
  │   │   │   ├── Screenshot 2026-07-01 222624.png
  │   │   │   ├── Screenshot 2026-07-01 223020.png
  │   │   │   ├── Screenshot 2026-07-02 000130.png
  │   │   │   ├── Screenshot 2026-07-02 213944.png
  │   │   │   ├── Screenshot 2026-07-02 215347.png
  │   │   │   ├── Screenshot 2026-07-02 215354.png
  │   │   │   ├── Screenshot 2026-07-03 122804.png
  │   │   │   ├── Screenshot 2026-07-04 010505.png
  │   │   │   ├── Screenshot 2026-07-04 025719.png
  │   │   │   ├── Screenshot 2026-07-04 025743.png
  │   │   │   ├── Screenshot 2026-07-04 025834.png
  │   │   │   ├── Screenshot 2026-07-04 030024.png
  │   │   │   ├── Screenshot 2026-07-04 030032.png
  │   │   │   ├── Screenshot 2026-07-04 030115.png
  │   │   │   ├── Screenshot 2026-07-04 031323.png
  │   │   │   ├── Screenshot 2026-07-04 031534.png
  │   │   │   ├── Screenshot 2026-07-04 035208.png
  │   │   │   ├── Screenshot 2026-07-04 221654.png
  │   │   │   ├── Screenshot 2026-07-04 221905.png
  │   │   │   ├── Screenshot 2026-07-04 222938.png
  │   │   │   ├── Screenshot 2026-07-04 230533.png
  │   │   │   ├── Screenshot 2026-07-05 172750.png
  │   │   │   ├── Screenshot 2026-07-05 172808.png
  │   │   │   ├── Screenshot 2026-07-05 172824.png
  │   │   │   ├── Screenshot 2026-07-05 181406.png
  │   │   │   ├── Screenshot 2026-07-05 181409.png
  │   │   │   ├── Screenshot 2026-07-05 181414.png
  │   │   │   ├── Screenshot 2026-07-05 182045.png
  │   │   │   ├── Screenshot 2026-07-05 191105.png
  │   │   │   ├── Screenshot 2026-07-05 201039.png
  │   │   │   ├── Screenshot 2026-07-06 215013.png
  │   │   │   ├── Screenshot 2026-07-06 220200.png
  │   │   │   ├── Screenshot 2026-07-06 220415.png
  │   │   │   ├── Screenshot 2026-07-06 220426.png
  │   │   │   ├── Screenshot 2026-08-28 014724.png
  │   │   │   ├── Screenshot 2026-08-28 015319.png
  │   │   │   ├── Screenshot 2026-08-28 020245.png
  │   │   │   ├── Screenshot 2026-09-02 234821.png
  │   │   │   ├── Screenshot 2026-09-03 105641.png
  │   │   │   ├── Screenshot 2026-09-03 105836.png
  │   │   │   ├── Screenshot 2026-09-03 105843.png
  │   │   │   ├── Screenshot 2026-09-03 105848.png
  │   │   │   ├── Screenshot 2026-09-03 110300.png
  │   │   │   ├── Screenshot 2026-09-03 110927.png
  │   │   │   ├── Screenshot 2026-09-03 111317.png
  │   │   │   ├── Screenshot 2026-09-03 111403.png
  │   │   │   ├── Screenshot 2026-09-03 111715.png
  │   │   │   ├── Screenshot 2026-09-03 112101.png
  │   │   │   ├── Screenshot 2026-09-03 112351.png
  │   │   │   ├── Screenshot 2026-09-03 112652.png
  │   │   │   ├── Screenshot 2026-09-03 113630.png
  │   │   │   ├── Screenshot 2026-09-03 114240.png
  │   │   │   ├── Screenshot 2026-09-03 114303.png
  │   │   │   ├── Screenshot 2026-09-03 120126.png
  │   │   │   ├── Screenshot 2026-09-03 120151.png
  │   │   │   ├── Screenshot 2026-09-03 120158.png
  │   │   │   ├── Screenshot 2026-09-04 140823.png
  │   │   │   ├── Screenshot 2026-09-04 202622.png
  │   │   │   ├── Screenshot 2026-09-04 202629.png
  │   │   │   ├── Screenshot 2026-09-04 202635.png
  │   │   │   ├── Screenshot 2026-09-04 202639.png
  │   │   │   ├── Screenshot 2026-09-04 202644.png
  │   │   │   ├── Screenshot 2026-09-04 202649.png
  │   │   │   ├── Screenshot 2026-09-04 202835.png
  │   │   │   ├── Screenshot 2026-09-04 202842.png
  │   │   │   ├── Screenshot 2026-09-04 202859.png
  │   │   │   ├── Screenshot 2026-09-04 202904.png
  │   │   │   ├── Screenshot 2026-09-04 202909.png
  │   │   │   ├── Screenshot 2026-09-04 202914.png
  │   │   │   ├── Screenshot 2026-09-06 193100.png
  │   │   │   ├── Screenshot 2026-09-06 194952.png
  │   │   │   ├── Screenshot 2026-09-06 195634.png
  │   │   │   ├── Screenshot 2026-09-06 200000.png
  │   │   │   ├── Screenshot 2026-09-06 200350.png
  │   │   │   ├── Screenshot 2026-09-06 200442.png
  │   │   │   ├── Screenshot 2026-09-06 200624.png
  │   │   │   ├── Screenshot 2026-09-06 201100.png
  │   │   │   ├── Screenshot 2026-09-06 201239.png
  │   │   │   ├── Screenshot 2026-09-06 201249.png
  │   │   │   ├── Screenshot 2026-09-06 201257.png
  │   │   │   ├── Screenshot 2026-09-06 232754.png
  │   │   │   ├── Screenshot 2026-09-06 232824.png
  │   │   │   ├── Screenshot 2026-09-07 010626.png
  │   │   │   ├── Screenshot 2026-09-07 120536.png
  │   │   │   ├── Screenshot 2026-09-07 120743.png
  │   │   │   ├── Screenshot 2026-09-07 120816.png
  │   │   │   ├── Screenshot 2026-09-07 121122.png
  │   │   │   ├── Screenshot 2026-09-07 121349.png
  │   │   │   ├── Screenshot 2026-09-07 121558.png
  │   │   │   ├── Screenshot 2026-09-07 121609.png
  │   │   │   ├── Screenshot 2026-09-07 122203.png
  │   │   │   ├── Screenshot 2026-09-07 122216.png
  │   │   │   ├── Screenshot 2026-09-07 122317.png
  │   │   │   ├── Screenshot 2026-09-09 150815.png
  │   │   │   ├── Screenshot 2026-09-09 154521.png
  │   │   │   ├── Screenshot 2026-09-09 154741.png
  │   │   │   ├── Screenshot 2026-09-09 161200.png
  │   │   │   ├── Screenshot 2026-09-09 161205.png
  │   │   │   ├── Screenshot 2026-09-09 174846.png
  │   │   │   ├── Screenshot 2026-09-10 003322.png
  │   │   │   ├── Screenshot 2026-09-10 180330.png
  │   │   │   ├── Screenshot 2026-09-10 180508.png
  │   │   │   ├── Screenshot 2026-09-10 183846.png
  │   │   │   ├── Screenshot 2026-09-10 185944.png
  │   │   │   ├── Screenshot 2026-09-10 190014.png
  │   │   │   ├── Screenshot 2026-09-10 190024.png
  │   │   │   ├── Screenshot 2026-09-10 190033.png
  │   │   │   ├── Screenshot 2026-09-10 190045.png
  │   │   │   ├── Screenshot 2026-09-10 190054.png
  │   │   │   ├── Screenshot 2026-09-10 201338.png
  │   │   │   ├── Screenshot 2026-09-10 222518.png
  │   │   │   ├── Screenshot 2026-09-11 000534.png
  │   │   │   ├── Screenshot 2026-09-11 001513.png
  │   │   │   ├── Screenshot 2026-09-11 001542.png
  │   │   │   ├── Screenshot 2026-09-11 004426.png
  │   │   │   ├── Screenshot 2026-09-11 004538.png
  │   │   │   ├── Screenshot 2026-09-11 005210.png
  │   │   │   ├── Screenshot 2026-09-11 005555.png
  │   │   │   ├── Screenshot 2026-09-11 005844.png
  │   │   │   ├── Screenshot 2026-09-11 005929.png
  │   │   │   ├── Screenshot 2026-09-11 010253.png
  │   │   │   ├── Screenshot 2026-09-11 010453.png
  │   │   │   ├── Screenshot 2026-09-11 010458.png
  │   │   │   ├── Screenshot 2026-09-11 010503.png
  │   │   │   ├── Screenshot 2026-09-11 011919.png
  │   │   │   ├── Screenshot 2026-09-11 012403.png
  │   │   │   ├── Screenshot 2026-09-11 012521.png
  │   │   │   ├── Screenshot 2026-09-11 013546.png
  │   │   │   ├── Screenshot 2026-09-11 014255.png
  │   │   │   ├── Screenshot 2026-09-11 014305.png
  │   │   │   ├── Screenshot 2026-09-11 014608.png
  │   │   │   ├── Screenshot 2026-09-11 014713.png
  │   │   │   ├── Screenshot 2026-09-11 015116.png
  │   │   │   ├── Screenshot 2026-09-11 162739.png
  │   │   │   ├── Screenshot 2026-09-11 162819.png
  │   │   │   ├── Screenshot 2026-09-11 165720.png
  │   │   │   ├── Screenshot 2026-09-11 165737.png
  │   │   │   ├── Screenshot 2026-09-11 165747.png
  │   │   │   ├── Screenshot 2026-09-11 165801.png
  │   │   │   ├── Screenshot 2026-09-11 170027.png
  │   │   │   ├── Screenshot 2026-09-11 170040.png
  │   │   │   ├── Screenshot 2026-09-11 170048.png
  │   │   │   ├── Screenshot 2026-09-11 170249.png
  │   │   │   ├── Screenshot 2026-09-15 233618.png
  │   │   │   ├── Screenshot 2026-09-15 235047.png
  │   │   │   ├── Screenshot 2026-09-16 104620.png
  │   │   │   ├── Screenshot 2026-09-17 221421.png
  │   │   │   ├── Screenshot 2026-09-17 222009.png
  │   │   │   ├── Screenshot 2026-09-17 225002.png
  │   │   │   ├── Screenshot 2026-09-17 225011.png
  │   │   │   ├── Screenshot 2026-09-17 225448.png
  │   │   │   ├── Screenshot 2026-09-17 225455.png
  │   │   │   ├── Screenshot 2026-09-17 230340.png
  │   │   │   ├── Screenshot 2026-09-17 230610.png
  │   │   │   ├── Screenshot 2026-09-17 233547.png
  │   │   │   ├── Screenshot 2026-09-17 234141.png
  │   │   │   ├── Screenshot 2026-09-17 234158.png
  │   │   │   ├── Screenshot 2026-09-17 234212.png
  │   │   │   ├── Screenshot 2026-09-18 005509.png
  │   │   │   ├── Screenshot 2026-09-18 112230.png
  │   │   │   ├── Screenshot 2026-09-18 113755.png
  │   │   │   ├── Screenshot 2026-09-19 214428.png
  │   │   │   ├── Screenshot 2026-09-19 214504.png
  │   │   │   ├── Screenshot 2026-09-19 214626.png
  │   │   │   ├── Screenshot 2026-09-19 214718.png
  │   │   │   ├── Screenshot 2026-09-19 221224.png
  │   │   │   ├── Screenshot 2026-09-19 221311.png
  │   │   │   ├── Screenshot 2026-09-19 222615.png
  │   │   │   ├── Screenshot 2026-09-20 022255.png
  │   │   │   ├── Screenshot 2026-09-20 022258.png
  │   │   │   ├── Screenshot 2026-09-20 022325.png
  │   │   │   ├── Screenshot 2026-09-20 022342.png
  │   │   │   ├── Screenshot 2026-09-20 022559.png
  │   │   │   ├── Screenshot 2026-09-20 022610.png
  │   │   │   ├── Screenshot 2026-09-20 022620.png
  │   │   │   ├── Screenshot 2026-09-20 022638.png
  │   │   │   ├── Screenshot 2026-09-20 023047.png
  │   │   │   ├── Screenshot 2026-09-20 023518.png
  │   │   │   ├── Screenshot 2026-09-20 023559.png
  │   │   │   ├── Screenshot 2026-09-20 023807.png
  │   │   │   ├── Screenshot 2026-09-20 023811.png
  │   │   │   ├── Screenshot 2026-09-20 023814.png
  │   │   │   ├── Screenshot 2026-09-20 145823.png
  │   │   │   ├── Screenshot 2026-09-20 150125.png
  │   │   │   ├── Screenshot 2026-09-20 151051.png
  │   │   │   ├── Screenshot 2026-09-20 151106.png
  │   │   │   ├── Screenshot 2026-09-20 151118.png
  │   │   │   ├── Screenshot 2026-09-20 151128.png
  │   │   │   ├── Screenshot 2026-09-20 151141.png
  │   │   │   ├── Screenshot 2026-09-20 151746.png
  │   │   │   ├── Screenshot 2026-09-20 151758.png
  │   │   │   ├── Screenshot 2026-09-20 151807.png
  │   │   │   ├── Screenshot 2026-09-20 151815.png
  │   │   │   ├── Screenshot 2026-09-20 151826.png
  │   │   │   ├── Screenshot 2026-09-20 151849.png
  │   │   │   ├── Screenshot_2026-08-28_014145.png
  │   │   │   ├── Screenshot_2026-08-28_014206.png
  │   │   │   ├── qt-ui-2026-08-12-234248.png
  │   │   │   ├── qt-ui-2026-08-12-234601.png
  │   │   │   ├── qt-ui-2026-08-13-003704.png
  │   │   │   ├── qt-ui-2026-08-13-004222.png
  │   │   │   ├── qt-ui-2026-08-13-005414.png
  │   │   │   ├── qt-ui-2026-08-13-010056.png
  │   │   │   ├── qt-ui-2026-08-13-013942.png
  │   │   │   ├── qt-ui-2026-08-13-014047.png
  │   │   │   ├── qt-ui-2026-08-13-014333.png
  │   │   │   ├── qt-ui-2026-08-13-014828.png
  │   │   │   ├── qt-ui-2026-08-13-015151.png
  │   │   │   ├── qt-ui-2026-08-13-015535.png
  │   │   │   ├── qt-ui-2026-08-13-023656.png
  │   │   │   ├── qt-ui-2026-08-13-024251.png
  │   │   │   ├── qt-ui-2026-08-13-152422.png
  │   │   │   ├── qt-ui-2026-08-13-152935.png
  │   │   │   ├── qt-ui-2026-08-13-153334.png
  │   │   │   ├── qt-ui-2026-08-13-153458.png
  │   │   │   ├── qt-ui-2026-08-13-155508.png
  │   │   │   ├── qt-ui-2026-08-13-160601.png
  │   │   │   ├── qt-ui-2026-08-13-174028.png
  │   │   │   ├── qt-ui-2026-08-13-183526.png
  │   │   │   ├── qt-ui-2026-08-13-183539.png
  │   │   │   ├── qt-ui-2026-08-13-184406.png
  │   │   │   ├── qt-ui-2026-08-13-185046.png
  │   │   │   ├── qt-ui-2026-08-13-194258.png
  │   │   │   ├── qt-ui-2026-08-13-200344.png
  │   │   │   ├── qt-ui-2026-08-13-201746.png
  │   │   │   ├── qt-ui-2026-08-14-130125.png
  │   │   │   ├── qt-ui-2026-08-14-130718.png
  │   │   │   ├── qt-ui-2026-08-14-170026.png
  │   │   │   ├── qt-ui-2026-08-14-170031.png
  │   │   │   ├── qt-ui-2026-08-14-171112.png
  │   │   │   ├── qt-ui-2026-08-14-172424.png
  │   │   │   ├── qt-ui-2026-08-14-172719.png
  │   │   │   ├── qt-ui-2026-08-14-174120.png
  │   │   │   ├── qt-ui-2026-08-14-174357.png
  │   │   │   ├── qt-ui-2026-08-14-192838.png
  │   │   │   ├── qt-ui-2026-08-14-193007.png
  │   │   │   ├── qt-ui-2026-08-14-193047.png
  │   │   │   ├── qt-ui-2026-08-14-193827.png
  │   │   │   ├── qt-ui-2026-08-14-193919.png
  │   │   │   ├── qt-ui-2026-08-14-211342.png
  │   │   │   ├── qt-ui-2026-08-14-211411.png
  │   │   │   ├── qt-ui-2026-08-14-211419.png
  │   │   │   ├── qt-ui-2026-08-14-211425.png
  │   │   │   ├── qt-ui-2026-08-14-211443.png
  │   │   │   ├── qt-ui-2026-08-14-211453.png
  │   │   │   ├── qt-ui-2026-08-16-213817.png
  │   │   │   ├── qt-ui-2026-08-16-214003.png
  │   │   │   ├── qt-ui-2026-08-16-214859.png
  │   │   │   ├── qt-ui-2026-08-16-215140.png
  │   │   │   ├── qt-ui-2026-08-16-215420.png
  │   │   │   ├── qt-ui-2026-08-16-220007.png
  │   │   │   ├── qt-ui-2026-08-16-220802.png
  │   │   │   ├── qt-ui-2026-08-16-220859.png
  │   │   │   ├── qt-ui-2026-08-17-164332.png
  │   │   │   ├── qt-ui-2026-08-17-185720.png
  │   │   │   ├── qt-ui-2026-08-17-185752.png
  │   │   │   ├── qt-ui-2026-08-18-115635.png
  │   │   │   ├── qt-ui-2026-08-18-115700.png
  │   │   │   ├── qt-ui-2026-08-18-115744.png
  │   │   │   ├── qt-ui-2026-08-18-115810.png
  │   │   │   ├── qt-ui-2026-08-18-160724.png
  │   │   │   ├── qt-ui-2026-08-27-102017.png
  │   │   │   ├── qt-ui-2026-08-27-231106.png
  │   │   │   ├── qt-ui-2026-08-27-231147.png
  │   │   │   ├── qt-ui-2026-08-27-231205.png
  │   │   │   ├── qt-ui-2026-08-27-234622.png
  │   │   │   ├── qt-ui-2026-08-27-235125.png
  │   │   │   ├── qt-ui-2026-08-27-235358.png
  │   │   │   ├── qt-ui-2026-08-27-235856.png
  │   │   │   ├── qt-ui-2026-08-28-000016.png
  │   │   │   ├── qt-ui-2026-08-28-000024.png
  │   │   │   ├── qt-ui-2026-08-28-000035.png
  │   │   │   ├── qt-ui-2026-08-28-000051.png
  │   │   │   ├── qt-ui-2026-08-28-000059.png
  │   │   │   ├── qt-ui-2026-08-28-000114.png
  │   │   │   ├── qt-ui-2026-08-28-000119.png
  │   │   │   ├── qt-ui-2026-08-28-000125.png
  │   │   │   └── qt-ui-2026-08-28-001903.png
  │   │   ├── README.md
  │   │   ├── attendance-rules.md
  │   │   ├── backup-restore-export.md
  │   │   ├── enrollment-and-scanning.md
  │   │   ├── first-run-wizard.md
  │   │   ├── installation-guide.md
  │   │   ├── project-overview.md
  │   │   ├── roles-and-permissions.md
  │   │   ├── testing-results.md
  │   │   ├── v3-workflows.md
  │   │   └── workflows.md
  │   ├── _inbox
  │   │   └── README.md
  │   ├── generated
  │   │   ├── APP_INVENTORY.md
  │   │   ├── APP_INVENTORY_UI_MAP.md
  │   │   ├── ARCHITECTURE.md
  │   │   ├── DATABASE.md
  │   │   ├── FILE_INVENTORY.md
  │   │   ├── FIRMWARE.md
  │   │   ├── GUI.md
  │   │   ├── INDEX.md
  │   │   ├── PROJECT_FORENSIC_AUDIT.md
  │   │   ├── PROJECT_OVERVIEW.md
  │   │   ├── README.md
  │   │   ├── REPOSITORY_AUDIT.md
  │   │   ├── SERIAL_PROTOCOL.md
  │   │   └── TESTING.md
  │   ├── CODE_METRICS.csv
  │   ├── CODE_METRICS.md
  │   ├── Documentation-Inventory.md
  │   ├── Documentation-Overhaul.md
  │   ├── ENROLLMENT_REGRESSION_DIAGNOSTIC.md
  │   ├── INDEX.md
  │   ├── README.md
  │   ├── REGRESSION_INVESTIGATION_SUMMARY.md
  │   ├── ROOT_CAUSE_ANALYSIS.md
  │   ├── SECURITY_AUDIT_REPORT.md
  │   ├── SECURITY_REMEDIATION_REPORT.md
  │   ├── Screenshot 2026-09-17 233547.png
  │   ├── TROUBLESHOOTING.md
  │   ├── audit_file_inventory.csv
  │   ├── dsis_prototype.html
  │   └── notes.txt
  ├── driver
  │   └── Install_CP210x_Driver.bat
  ├── firmware
  │   ├── ESP32_DSIS_AllInOne
  │   │   ├── src
  │   │   │   └── rfid
  │   │   │       ├── CardDetector.cpp
  │   │   │       ├── CardDetector.h
  │   │   │       ├── ClassicAdapter.cpp
  │   │   │       ├── ClassicAdapter.h
  │   │   │       ├── Type2Adapter.cpp
  │   │   │       └── Type2Adapter.h
  │   │   └── ESP32_DSIS_AllInOne.ino
  │   ├── ESP32_Fingerprint_AllInOne
  │   │   └── ESP32_Fingerprint_AllInOne.ino
  │   ├── attendance
  │   │   └── attendance.ino
  │   ├── delete
  │   │   └── delete.ino
  │   ├── enroll
  │   │   └── enroll.ino
  │   ├── rc522_dumpinfo_test
  │   │   └── rc522_dumpinfo_test.ino
  │   ├── rc522_read
  │   │   └── rc522_read.ino
  │   ├── rc522_readwrite
  │   │   └── rc522_readwrite.ino
  │   ├── rc522_test
  │   │   └── rc522_test.ino
  │   ├── rc522_write
  │   │   └── rc522_write.ino
  │   └── test
  │       └── fingerprint_check
  │           └── fingerprint_check.ino
  ├── python
  │   ├── core
  │   │   ├── __init__.py
  │   │   ├── attendance.py
  │   │   ├── attendance_calendar.py
  │   │   ├── attendance_status.py
  │   │   ├── auth.py
  │   │   ├── commands.py
  │   │   ├── database.py
  │   │   ├── device_discovery.py
  │   │   ├── firmware_helper.py
  │   │   ├── logger.py
  │   │   ├── permissions.py
  │   │   ├── rfid_card.py
  │   │   ├── serial_handler.py
  │   │   ├── setup_wizard.py
  │   │   └── utils.py
  │   ├── gui
  │   │   ├── legacy
  │   │   │   ├── bfeas_app2.py
  │   │   │   └── reports_table_page.py
  │   │   └── __init__.py
  │   ├── gui_qt
  │   │   └── __init__.py
  │   ├── gui_web
  │   │   ├── v2_reference
  │   │   │   ├── gui_qt
  │   │   │   │   ├── pages
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── attendance_page.py
  │   │   │   │   │   ├── dashboard_page.py
  │   │   │   │   │   ├── logs_page.py
  │   │   │   │   │   ├── reports_page.py
  │   │   │   │   │   ├── settings_page.py
  │   │   │   │   │   └── students_page.py
  │   │   │   │   ├── widgets
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── sidebar.py
  │   │   │   │   │   └── stat_card.py
  │   │   │   │   ├── workers
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── connection_worker.py
  │   │   │   │   │   └── serial_worker.py
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── main_qt.py
  │   │   │   │   ├── main_window.py
  │   │   │   │   ├── theme.qss
  │   │   │   │   └── theme_light.qss
  │   │   │   └── README.md
  │   │   ├── web
  │   │   │   ├── app.js
  │   │   │   ├── index.html
  │   │   │   └── styles.css
  │   │   ├── __init__.py
  │   │   ├── api.py
  │   │   ├── main_web.py
  │   │   └── perf_profiler.py
  │   ├── services
  │   │   ├── __init__.py
  │   │   ├── attendance_service.py
  │   │   └── student_service.py
  │   ├── __init__.py
  │   ├── config.py
  │   ├── main.py
  │   └── settings_store.py
  ├── system
  │   └── python
  │       └── README.md
  ├── tests
  │   ├── Prototype
  │   │   ├── Python
  │   │   │   ├── actual_ui_prototype.py
  │   │   │   ├── combined_ui.py
  │   │   │   ├── hybrid_window.py
  │   │   │   ├── original_window.py
  │   │   │   ├── prototype_window.py
  │   │   │   └── task_manager_window.py
  │   │   ├── tests
  │   │   │   ├── test_actual_ui_prototype.py
  │   │   │   ├── test_combined_ui.py
  │   │   │   ├── test_hybrid_prototype.py
  │   │   │   ├── test_original_ui.py
  │   │   │   ├── test_qt_prototype.py
  │   │   │   └── test_task_manager_variant.py
  │   │   ├── hybrid_window.py
  │   │   ├── original_ui.py
  │   │   ├── run_combined_ui.py
  │   │   ├── run_hybrid_prototype.py
  │   │   ├── run_original_ui_display.py
  │   │   ├── run_qt_prototype.py
  │   │   └── run_task_manager_variant.py
  │   ├── _archives
  │   │   ├── ESP32 R307 Finger print Sensor
  │   │   │   ├── ESP32_enroll_R307_finger_Print
  │   │   │   │   └── ESP32_enroll_R307_finger_Print.ino
  │   │   │   └── esp32_fingerprint_check_R307
  │   │   │       └── esp32_fingerprint_check_R307.ino
  │   │   ├── ESP32 R307 Finger print Sensor.zip
  │   │   ├── gui_qt_redesign.zip
  │   │   └── qt_gui_interactive_bundle.zip
  │   ├── _reference
  │   │   ├── ENHANCED_GUI_GUIDE.txt
  │   │   ├── HOW_TO_RUN_TEST_GUI.txt
  │   │   ├── QUICK_REFERENCE.txt
  │   │   ├── README_QT_GUI_TEST.md
  │   │   ├── README_TEST_GUI.txt
  │   │   ├── TEST_GUI_README.md
  │   │   ├── VISUAL_GUIDE.txt
  │   │   └── run_qt_gui_test.bat
  │   ├── legacy
  │   │   ├── raw_serial_diagnostic
  │   │   │   └── raw_serial_diagnostic.ino
  │   │   ├── phase2_databasev1.py
  │   │   ├── phase2_databasev2.py
  │   │   ├── phase2_databasev3.py
  │   │   ├── phase2_databasev4.py
  │   │   └── phase2_serial_test.py
  │   ├── manual_hardware_scripts
  │   │   ├── test_debug_raw_lines.py
  │   │   ├── test_enrollment_with_worker.py
  │   │   ├── test_gui_demo.py
  │   │   └── test_minimal_enroll.py
  │   ├── app_test.py
  │   ├── comprehensive_test.py
  │   ├── conftest.py
  │   ├── physical_esp32_smoke.py
  │   ├── qt_gui_interactive.py
  │   ├── test_active_firmware_protocol.py
  │   ├── test_attendance_export_rows.py
  │   ├── test_attendance_parsing.py
  │   ├── test_attendance_processor.py
  │   ├── test_attendance_refresh.py
  │   ├── test_attendance_status.py
  │   ├── test_attendance_ui_regressions.py
  │   ├── test_attendance_ui_utils.py
  │   ├── test_auto_port_probe.py
  │   ├── test_bfeas_app2_import.py
  │   ├── test_button_in_context.py
  │   ├── test_database_features.py
  │   ├── test_database_reset.py
  │   ├── test_database_security.py
  │   ├── test_dialog_enrollment_integration.py
  │   ├── test_dialog_handlers.py
  │   ├── test_enrollment_debug.py
  │   ├── test_enrollment_dialog_ux.py
  │   ├── test_error_message_sanitization.py
  │   ├── test_firmware_helper.py
  │   ├── test_gui_settings_integration.py
  │   ├── test_gui_shutdown.py
  │   ├── test_gui_web_smoke.py
  │   ├── test_mode_exclusivity.py
  │   ├── test_permissions_and_attendance_tagging.py
  │   ├── test_project_structure.py
  │   ├── test_qt_attendance_page.py
  │   ├── test_qt_enrollment_flow.py
  │   ├── test_qt_main_window.py
  │   ├── test_qt_serial_worker.py
  │   ├── test_qt_settings_logs.py
  │   ├── test_qt_shell.py
  │   ├── test_qt_students_page.py
  │   ├── test_qt_thread_exception_handling.py
  │   ├── test_reports_page_import.py
  │   ├── test_responsive_layout.py
  │   ├── test_sensor_failure_handshake_recovery.py
  │   ├── test_serial_handler_host_gate.py
  │   ├── test_serial_monitor_boot_banner.py
  │   ├── test_serial_troubleshooting.py
  │   ├── test_settings_persistence.py
  │   ├── test_settings_toggles.py
  │   ├── test_student_input_regression.py
  │   ├── test_student_input_validation.py
  │   ├── test_theme_switching.py
  │   ├── test_type_hints.py
  │   ├── test_v3_authentication.py
  │   ├── test_vidpid_normalization.py
  │   ├── tmp_card_claim_test.db
  │   └── whs_dashboard.py
  ├── tools
  │   ├── _database_refactor.py
  │   ├── archive_unused_python.py
  │   ├── copilot_forensic_search.py
  │   ├── debug_db_connections.py
  │   ├── fingerprint_portable.spec
  │   ├── list_files.bat
  │   ├── runtime_manager.py
  │   ├── serial_handler_connect_probe.py
  │   ├── serial_pipeline_tester.py
  │   ├── serial_worker_probe.py
  │   └── verify_gui_startup.py
  ├── .gitattributes
  ├── .gitignore
  ├── CODE_OF_CONDUCT.md
  ├── CONTRIBUTING.md
  ├── INSTALLATION.md
  ├── LICENSE
  ├── PORTABLE_BUILD.md
  ├── README.md
  ├── RELEASE.md
  ├── SECURITY.md
  ├── install_requirements.bat
  ├── pytest.ini
  ├── requirements.txt
  ├── run_web_gui.bat
  └── run_web_gui.py
```

## 2. Source symbol tree

The next sections expand source files into the functions/classes currently found in the maintained code paths. Generated, binary, image, and documentation files do not have runtime functions and therefore remain represented by the complete file tree above.

### 2.1 Maintained production source

_Production symbol expansion follows in the next generated sections._


### 2.1A Production symbols — firmware + core foundations

```text
firmware/ESP32_DSIS_AllInOne/ESP32_DSIS_AllInOne.ino
  ├── function hexValue()
  ├── function ledBrightness()
  ├── function ledOff()
  ├── function getPriorityForState()
  ├── function requestLedState()
  ├── function restoreLedStateIfNeeded()
  ├── function handleHostStatus()
  ├── function parseJsonStringField()
  ├── function emitJsonStatus()
  ├── function emitJsonAttendanceMatch()
  ├── function emitJsonAttendanceUnknown()
  ├── function emitJsonAttendanceLowConfidence()
  ├── function uidToString()
  ├── function bytesToHex()
  ├── function emitJsonCardMatch()
  ├── function emitJsonCardUnreadable()
  ├── function emitJsonCardWriteResult()
  ├── function emitJsonCardKeyCheck()
  ├── function beginLedManager()
  ├── function ledReady()
  ├── function ledScan()
  ├── function ledEnroll()
  ├── function ledSuccess()
  ├── function ledError()
  ├── function ledSleep()
  ├── function ledFirmware()
  ├── function ledHostConnected()
  ├── function ledHostDisconnected()
  ├── function computeBootBrightness()
  ├── function updateLed()
  ├── function setup()
  ├── function loop()
  ├── function handleCommand()
  ├── function fingerprintExists()
  ├── function findNextAvailableId()
  ├── function checkEnrollmentCancel()
  ├── function enrollFinger()
  ├── function SCAN()
  ├── function CARD()
  └── function printHelp()

firmware/ESP32_DSIS_AllInOne/src/rfid/CardDetector.cpp
  └── function detectRfidCard()

firmware/ESP32_DSIS_AllInOne/src/rfid/CardDetector.h
  └── [no class/function definitions detected]

firmware/ESP32_DSIS_AllInOne/src/rfid/ClassicAdapter.cpp
  ├── function classicKeyCandidateCount()
  ├── function classicKeyCandidate()
  ├── function sameUid()
  ├── function authenticateClassicCard()
  ├── function readClassicPayload()
  └── function writeClassicPayload()

firmware/ESP32_DSIS_AllInOne/src/rfid/ClassicAdapter.h
  └── [no class/function definitions detected]

firmware/ESP32_DSIS_AllInOne/src/rfid/Type2Adapter.cpp
  ├── function readType2Payload()
  └── function writeType2Payload()

firmware/ESP32_DSIS_AllInOne/src/rfid/Type2Adapter.h
  └── [no class/function definitions detected]

python/__init__.py
  └── [no class/function definitions detected]

python/config.py
  ├── def _resolve_project_root()
  ├── def _env_flag()
  ├── def _env_int()
  ├── def _env_path()
  ├── class AppConfig()
  ├── def from_env()
  ├── def get_config()
  ├── def discover_serial_ports()
  ├── def get_default_com_port()
  └── def get_com_port()

python/core/__init__.py
  └── [no class/function definitions detected]

python/core/attendance.py
  ├── class ScanResult()
  ├── class ScanOutcome()
  ├── def to_dict()
  ├── class AttendanceProcessor()
  ├── def __init__()
  ├── def process_line()
  ├── def reset()
  ├── def lookup_student()
  ├── def lookup_card_student()
  ├── def all_students()
  ├── def _handle_unknown_scan()
  ├── def _handle_unknown_card_scan()
  ├── def _handle_card_scan()
  ├── def _handle_confidence_scan()
  ├── def _handle_json_match_scan()
  ├── def _parse_json_int()
  ├── def _parse_int_value()
  ├── def _is_in_cooldown()
  ├── def _cooldown_reason()
  └── def _log_and_record()

python/core/attendance_calendar.py
  ├── def _is_valid_date_string()
  ├── def _is_valid_time_string()
  ├── def _minutes()
  ├── def get_calendar()
  ├── def get_entry()
  ├── def is_non_school_day()
  ├── def get_schedule_for_date()
  ├── def validate_entry()
  ├── def set_entry()
  └── def remove_entry()

python/core/attendance_status.py
  ├── def _minutes()
  └── def calculate_attendance_status()

python/core/auth.py
  ├── def hash_password()
  ├── def verify_password()
  ├── def has_password_set()
  ├── def validate_new_password()
  └── def set_initial_password()

python/core/commands.py
  ├── def cmd_scan()
  ├── def cmd_stop()
  ├── def build_enroll_command()
  ├── def cmd_enroll()
  ├── def cmd_delete()
  ├── def cmd_wipe()
  ├── def cmd_list()
  ├── def cmd_card_write()
  ├── def cmd_card_write_hex()
  └── def cmd_card_erase()
```

### 2.2 Tests

_Test symbol expansion follows._

### 2.3 Archive / historical source

_Archive files are retained in the complete repository tree. Their symbols are historical/reference code rather than part of the maintained V3 runtime._

## 3. Architecture reading order

```text
run_web_gui.py
    ↓
python/gui_web/main_web.py
    ↓
python/gui_web/api.py
    ↓
python/core/*
    ├── auth
    ├── permissions
    ├── serial_handler
    ├── device_discovery
    ├── attendance
    ├── attendance_status
    ├── attendance_calendar
    ├── database
    ├── rfid_card
    ├── commands
    ├── firmware_helper
    ├── logger
    ├── setup_wizard
    └── utils
    ↓
python/services/*
    ↓
SQLite / local runtime data
    +
USB serial 115200
    ↓
firmware/ESP32_DSIS_AllInOne/*
    ├── AS608 fingerprint branch
    └── RC522 RFID branch
         ├── CardDetector
         ├── ClassicAdapter
         └── Type2Adapter
```

## 4. Symbol legend

- `class X` — Python class or C++ class/struct detected in source.
- `def X()` — Python function/method.
- C++/Arduino entries are concrete function definitions found in the sketch/header/source.
- A function list is a static source inventory, not a call graph.
- Historical implementations are not silently merged with V3; active and archived code remain separate.

