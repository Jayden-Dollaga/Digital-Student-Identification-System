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
  │   │   ├── PROJECT_ARCHITECTURE_TREE.md
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
  └── run_web_gui.py`

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


### 2.1B Production symbols — backend + GUI bridge

```text
python/core/database.py
  ├── class ValidationState()
  ├── class FieldValidationResult()
  ├── def _is_valid_name_character()
  ├── def _is_valid_student_name()
  ├── def _collect_unsupported_characters()
  ├── def _collect_unsupported_name_characters()
  ├── def _format_unsupported_characters()
  ├── class ManagedConnection()
  ├── def __init__()
  ├── def __enter__()
  ├── def __exit__()
  ├── def close()
  ├── def __getattr__()
  ├── class AttendanceRow()
  ├── class StudentRow()
  ├── def export_name_sort_key()
  ├── def get_connection()
  ├── def _row_dicts()
  ├── def _student_select_sql()
  ├── def normalize_card_uid()
  ├── def _student_card_uid_column_exists()
  ├── def init_database()
  ├── def _migrate_attendance_event_type()
  ├── def validate_student_input()
  ├── def get_student_field_feedback()
  ├── def add_feedback()
  ├── def check_name()
  ├── def check_token()
  ├── def add_student()
  ├── def update_student()
  ├── def replace_student_fingerprint()
  ├── def delete_student()
  ├── def clear_all_students()
  ├── def get_student()
  ├── def get_student_by_card_uid()
  ├── def bind_student_card()
  ├── def clear_student_card()
  ├── def get_all_students()
  ├── def get_student_count()
  ├── def register_student()
  ├── def import_students_from_list()
  ├── def log_attendance()
  ├── def get_attendance_today()
  ├── def get_today_attendance_info()
  ├── def get_attendance_all()
  ├── def get_attendance_paginated()
  ├── def get_attendance_count_today()
  ├── def get_daily_attendance_summary()
  ├── def get_attendance_by_date()
  ├── def clear_all_attendance()
  ├── def clear_all_data()
  ├── def get_attendance_by_student()
  ├── def get_students_by_grade_section()
  ├── def count_attendance_by_date()
  ├── def get_attendance_statistics()
  ├── def get_students_statistics()
  ├── def export_attendance_range()
  ├── def export_attendance_range_with_time_in_out()
  ├── def export_attendance_rows_with_time_in_out()
  ├── def generate_statistics_report()
  ├── def _save_chart()
  ├── def generate_attendance_chart()
  ├── def generate_section_chart()
  ├── def generate_grade_chart()
  ├── def backup_database()
  ├── def _is_path_within_directory()
  ├── def _is_valid_sqlite_db_file()
  ├── def restore_database()
  ├── def list_backups()
  └── def auto_backup_if_needed()

python/core/device_discovery.py
  ├── def list_serial_ports()
  ├── def _score_port_info()
  ├── def _ordered_candidate_ports()
  ├── def add_port()
  ├── def _parse_json_line()
  ├── def _validate_handshake()
  ├── def _probe_port()
  ├── def _accept_handshake()
  └── def discover_device()

python/core/firmware_helper.py
  ├── def discover_firmware_candidates()
  ├── def find_firmware_binary()
  ├── def find_arduino_firmware()
  ├── def esptool_available()
  ├── def build_upload_command()
  ├── def upload_firmware()
  └── def upload_firmware_with_progress()

python/core/logger.py
  ├── class AppFormatter()
  ├── def formatTime()
  ├── def format()
  ├── def _derive_source()
  ├── def _format_structured()
  ├── def _prune_old_logs()
  ├── def _configure_logger()
  ├── def _log_with_structured()
  ├── def debug()
  ├── def info()
  ├── def success()
  ├── def warning()
  ├── def error()
  ├── def critical()
  ├── def exception()
  └── class LoggerProxy()

python/core/permissions.py
  ├── def set_session_role()
  ├── def touch_session()
  ├── def get_current_role()
  ├── def has_permission()
  ├── def has_role_permission()
  ├── def require_role()
  └── def require_permission()

python/core/rfid_card.py
  ├── def _decode_rfid_key()
  ├── def get_or_create_rfid_app_key()
  ├── def _normalize_card_uid()
  ├── def _payload_aad()
  ├── def encrypt_student_card_payload()
  └── def decrypt_student_card_payload()

python/core/serial_handler.py
  ├── def list_serial_ports()
  ├── def build_common_port_candidates()
  ├── class SerialHandler()
  ├── def __init__()
  ├── def pyserial_installed()
  ├── def list_available_ports()
  ├── def connect()
  ├── def disconnect()
  ├── def _send_host_connected()
  ├── def test_connection()
  ├── def send_command()
  ├── def reset_device()
  ├── def read_line()
  ├── def should_ignore()
  ├── def is_connected()
  ├── def auto_reconnect()
  ├── def _schedule_reconnect()
  ├── def _join_reconnect_thread()
  ├── def _reconnect_worker()
  └── def _attempt_connect()

python/core/setup_wizard.py
  ├── def get_next_step()
  └── def is_setup_complete()

python/core/utils.py
  ├── def parse_json_line()
  ├── def get_export_path()
  ├── def timestamp_filename()
  ├── def format_datetime()
  ├── def today_str()
  ├── def now_str()
  └── def format_attendance_display()

python/gui/__init__.py
  └── [no class/function definitions detected]

python/gui/legacy/bfeas_app2.py
  └── def main()

python/gui/legacy/reports_table_page.py
  ├── class ReportsPage()
  └── def __init__()

python/gui_qt/__init__.py
  └── [no class/function definitions detected]

python/gui_web/__init__.py
  └── [no class/function definitions detected]

python/gui_web/api.py
  ├── def _sanitize_csv_cell()
  ├── def _attendance_category()
  ├── def _student_label()
  ├── class _UILogHandler()
  ├── def __init__()
  ├── def emit()
  ├── class Api()
  ├── def _auto_backup_loop()
  ├── def start_background_tasks()
  ├── def stop_background_tasks()
  ├── def set_window()
  ├── def _choose_csv_path()
  ├── def _push()
  ├── def list_ports()
  ├── def list_ports_detailed()
  ├── def forget_saved_port()
  ├── def connect()
  ├── def disconnect()
  ├── def _disconnect_impl()
  ├── def get_connection_status()
  ├── def _operation_conflict()
  ├── def start_scan()
  ├── def stop_scan()
  ├── def start_rfid_register_session()
  ├── def stop_rfid_register_session()
  ├── def start_batch_rfid_erase()
  ├── def stop_batch_rfid_erase()
  ├── def _push_batch_erase_result()
  ├── def _handle_batch_rfid_erase_event()
  ├── def _handle_rfid_session_card_event()
  ├── def _clear_pending_rfid_registration()
  ├── def _push_rfid_registration_result()
  ├── def _handle_rfid_registration_tap()
  ├── def _handle_rfid_registration_write()
  ├── def start_enroll()
  ├── def validate_student_fields()
  ├── def cancel_enroll()
  ├── def discard_enrollment()
  ├── def delete_on_device()
  ├── def wipe_all_on_device()
  ├── def wipe_all_data()
  ├── def request_fingerprint_count()
  ├── def _start_read_loop()
  ├── def _stop_read_loop()
  ├── def _sync_connection_state()
  ├── def get_serial_troubleshooting()
  ├── def open_device_manager()
  ├── def open_driver_help()
  ├── def _read_loop()
  ├── def _parse_mode_line()
  ├── def _parse_scan_line()
  ├── def _parse_enroll_progress()
  ├── def _parse_wipe_progress()
  ├── def _parse_delete_progress()
  ├── def _parse_fingerprint_count()
  ├── def send_serial_command()
  ├── def reset_device()
  ├── def _append_serial_log()
  ├── def get_dashboard_stats()
  ├── def get_recent_activity()
  ├── def get_attendance()
  ├── def export_attendance_csv()
  ├── def get_students()
  ├── def get_student()
  ├── def save_student()
  ├── def bind_student_card()
  ├── def clear_student_card()
  ├── def delete_student()
  ├── def export_students_csv()
  ├── def _export_csv_rows()
  ├── def _rows_to_csv()
  ├── def get_attendance_evaluation()
  ├── def export_attendance_evaluation_csv()
  ├── def get_calendar_month()
  ├── def set_calendar_entry()
  ├── def remove_calendar_entry()
  ├── def get_statistics_report()
  ├── def export_statistics_report()
  ├── def list_backups()
  ├── def create_backup()
  ├── def restore_backup()
  ├── def get_settings()
  ├── def save_ui_settings()
  ├── def restore_default_settings()
  ├── def get_current_role()
  ├── def set_current_role()
  ├── def is_first_run_setup_required()
  ├── def complete_first_run_setup()
  ├── def get_setup_wizard_step()
  ├── def complete_setup_device_step()
  ├── def complete_setup_schedule_step()
  ├── def complete_setup_branding_step()
  ├── def authenticate_role()
  ├── def get_session_state()
  ├── def touch_session()
  ├── def lock_session()
  ├── def change_admin_password()
  ├── def get_role_permissions()
  ├── def open_log_folder()
  └── def get_app_log()
```


### 2.1C Production symbols — GUI, V2 references, profiler

```text
python/gui_web/main_web.py
  ├── def _logo_path()
  ├── def _handle_uncaught_exception()
  ├── def _handle_thread_exception()
  ├── def main()
  └── def _on_closed()

python/gui_web/perf_profiler.py
  ├── class PerfProfiler()
  ├── def __init__()
  ├── def start()
  ├── def stop()
  ├── def report()
  ├── def wrap()
  ├── class _Context()
  ├── def __enter__()
  └── def __exit__()

python/gui_web/v2_reference/gui_qt/__init__.py
  └── [no class/function definitions detected]

python/gui_web/v2_reference/gui_qt/main_qt.py
  ├── def _handle_uncaught_exception()
  ├── def _handle_thread_exception()
  ├── def _on_app_about_to_quit()
  ├── def _on_process_exit()
  ├── def apply_base_style()
  ├── def _build_palette()
  ├── def apply_theme()
  ├── def load_stylesheet()
  └── def main()

python/gui_web/v2_reference/gui_qt/main_window.py
  ├── class MainWindow()
  ├── def __init__()
  ├── def _configure_auto_backup_timer()
  ├── def _run_auto_backup_check()
  ├── def switch_page()
  ├── def _apply_role_permissions()
  ├── def _set_connect_button_state()
  ├── def on_connect_clicked()
  ├── def on_connect_result()
  ├── def on_connection_settings_changed()
  ├── class _LogBridge()
  ├── class _QtLogHandler()
  ├── def emit()
  ├── def _create_log_handler()
  ├── def on_connection_changed()
  ├── def on_scan_event()
  ├── def on_serial_error()
  ├── def on_scan_mode_changed()
  ├── def _update_scan_toggle_button()
  ├── def _set_scan_block_reason()
  ├── def _clear_scan_block_reason()
  ├── def _scan_command_blocked_reason()
  ├── def _can_start_scan()
  ├── def on_scan_toggle_clicked()
  ├── def update_connection_metadata()
  └── def closeEvent()

python/gui_web/v2_reference/gui_qt/pages/__init__.py
  └── [no class/function definitions detected]

python/gui_web/v2_reference/gui_qt/pages/attendance_page.py
  ├── class AttendancePage()
  ├── def __init__()
  ├── def _on_mode_changed()
  ├── def _is_recent_mode()
  ├── def _is_last_30_days_mode()
  ├── def refresh()
  ├── def _update_pagination_controls()
  ├── def on_prev_clicked()
  ├── def on_next_clicked()
  ├── def _populate()
  └── def on_scan_event()

python/gui_web/v2_reference/gui_qt/pages/dashboard_page.py
  ├── class DashboardPage()
  ├── def __init__()
  ├── def _format_item_text()
  ├── def refresh()
  ├── def refresh_dashboard()
  └── def on_scan_event()

python/gui_web/v2_reference/gui_qt/pages/logs_page.py
  ├── class LogsPage()
  ├── def __init__()
  ├── def console()
  ├── def monitor()
  ├── def clear()
  ├── def append_line()
  ├── def append_serial_line()
  ├── def append_record()
  ├── def set_connection_state()
  ├── def set_connection_info()
  ├── def clear_app_log()
  ├── def clear_monitor()
  ├── def pause_monitor()
  ├── def resume_monitor()
  ├── def _set_auto_scroll()
  ├── def send_command()
  ├── def send_list_command()
  ├── def reset_device()
  ├── def _append_app_text()
  └── def _append_serial_text()

python/gui_web/v2_reference/gui_qt/pages/reports_page.py
  ├── def _sanitize_csv_cell()
  ├── class ReportsPage()
  ├── def __init__()
  ├── def refresh_backup_list()
  ├── def refresh()
  ├── def refresh_report()
  ├── def on_export_clicked()
  ├── def on_backup_clicked()
  └── def on_restore_clicked()

python/gui_web/v2_reference/gui_qt/pages/settings_page.py
  ├── class SettingsPage()
  ├── def __init__()
  ├── def _section_label()
  ├── def refresh()
  ├── def refresh_connection_status()
  ├── def _update_permissions_label()
  ├── def _open_folder()
  ├── def _apply_theme()
  ├── def _populate_ports()
  ├── def _forget_saved_port()
  └── def on_save()

python/gui_web/v2_reference/gui_qt/pages/students_page.py
  ├── class EnrollmentState()
  ├── class EnrollDialog()
  ├── def __init__()
  ├── def _show_field_validation_feedback()
  ├── def _is_form_valid()
  ├── def _on_form_changed()
  ├── def _set_state()
  ├── def _on_primary_action()
  ├── def _start_enrollment()
  ├── def _save_student()
  ├── def _append_log_line()
  ├── def on_enroll_progress()
  ├── def _cleanup_before_close()
  ├── def on_cancel()
  ├── def get_values()
  ├── def closeEvent()
  ├── class StudentDetailsDialog()
  ├── class WipeDialog()
  ├── def on_confirm()
  ├── def on_wipe_progress()
  ├── def _show_done_state()
  ├── class ConfirmDeleteDialog()
  ├── def _send_next()
  ├── def on_delete_progress()
  ├── def _delete_local()
  ├── def _finish()
  ├── class StudentsPage()
  ├── def refresh()
  ├── def save_student_details()
  ├── def on_enroll_clicked()
  ├── def _selected_rows()
  ├── def on_delete_clicked()
  ├── def on_edit_clicked()
  └── def on_wipe_clicked()

python/gui_web/v2_reference/gui_qt/widgets/__init__.py
  └── [no class/function definitions detected]

python/gui_web/v2_reference/gui_qt/widgets/sidebar.py
  ├── class Sidebar()
  ├── def __init__()
  ├── def set_compact()
  ├── def is_compact()
  └── def set_enabled_pages()

python/gui_web/v2_reference/gui_qt/widgets/stat_card.py
  ├── class StatCard()
  ├── def __init__()
  └── def set_value()
```


### 2.1D Production symbols — remaining GUI, services, settings, tools

```text
python/gui_web/v2_reference/gui_qt/workers/__init__.py
  └── [no class/function definitions detected]

python/gui_web/v2_reference/gui_qt/workers/connection_worker.py
  ├── class ConnectionWorker()
  ├── def __init__()
  ├── def connect_to_device()
  ├── def disconnect_from_device()
  ├── def run()
  └── def stop()

python/gui_web/v2_reference/gui_qt/workers/serial_worker.py
  ├── class SerialWorker()
  ├── def __init__()
  ├── def run()
  ├── def _parse_mode_line()
  ├── def _process_line()
  ├── def _parse_enroll_progress()
  ├── def _parse_wipe_progress()
  ├── def _parse_delete_progress()
  ├── def _parse_fingerprint_count()
  └── def stop()

python/gui_web/web/app.js
  ├── function hasPermission()
  ├── function hasRole()
  ├── function refreshAdminOnlyVisibility()
  ├── function guardPermission()
  ├── function escapeHtml()
  ├── function whenApiReady()
  ├── function api()
  ├── function nav()
  ├── function applySessionState()
  ├── function togglePasswordField()
  ├── function renderWizardProgress()
  ├── function wizardGoToPreviousStep()
  ├── function openFirstRunSetupModal()
  ├── function submitFirstRunSetup()
  ├── function runSetupWizardRouter()
  ├── function openSetupDeviceStep()
  ├── function setupDeviceConnectClick()
  ├── function updateSetupDeviceStatus()
  ├── function completeSetupDeviceStep()
  ├── function updateWindowSizeMode()
  ├── function applySetupWeekdaySelection()
  ├── function attachSetupWeekdayToggles()
  ├── function openSetupScheduleStep()
  ├── function completeSetupScheduleStep()
  ├── function openSetupBrandingStep()
  ├── function completeSetupBrandingStep()
  ├── function openRoleAuthModal()
  ├── function closeRoleAuthModal()
  ├── function submitRoleAuth()
  ├── function requestRoleChange()
  ├── function lockSession()
  ├── function openChangePasswordModal()
  ├── function closeChangePasswordModal()
  ├── function changeAdminPassword()
  ├── function applyCompact()
  ├── function applySchoolName()
  ├── function toggleCompact()
  ├── function setStatus()
  ├── function toggleConnect()
  ├── function snapshotted()
  ├── function setConnectButtonsBusy()
  ├── function showSerialTroubleshooting()
  ├── function toggleScan()
  ├── function handleConnectionStatus()
  ├── function handleConnectionChanged()
  ├── function handleSerialError()
  ├── function handleDataChanged()
  ├── function handleModeChanged()
  ├── function handleFingerprintCount()
  ├── function handleScanResult()
  ├── function loadDashboard()
  ├── function todayStr()
  ├── function onPeriodChange()
  ├── function loadAttendanceEvaluation()
  ├── function formatEvalRangeLabel()
  ├── function renderAttendanceEvaluation()
  ├── function exportAttendanceEvaluationCsv()
  ├── function loadDashboardStats()
  ├── function loadRecentActivity()
  ├── function isKnownRow()
  ├── function rowToActivityTr()
  ├── function badgeClass()
  ├── function attendanceBadgeClass()
  ├── function loadAttendancePage()
  ├── function renderAttendanceRows()
  ├── function attendancePrevPage()
  ├── function attendanceNextPage()
  ├── function attendanceOnScanEvent()
  ├── function isoWeekToMonday()
  ├── function currentIsoWeek()
  ├── function formatWeekRange()
  ├── function updateExportWeekLabel()
  ├── function exportAttendanceCsv()
  ├── function loadStudentsPage()
  ├── function toggleStudentSelection()
  ├── function toggleAllStudentSelection()
  ├── function updateStudentSelectionUi()
  ├── function selectStudent()
  ├── function updateStudentDetailButtons()
  ├── function setManageRfidProgress()
  ├── function closeBatchRfidEraseDialog()
  ├── function openBatchRfidEraseDialog()
  ├── function closeManageRfidDialog()
  ├── function openManageRfidDialog()
  ├── function registerSelectedStudentCard()
  ├── function replaceSelectedStudentCard()
  ├── function unlinkSelectedStudentCard()
  ├── function showDestructiveConfirm()
  ├── function deleteSelectedStudent()
  ├── function deleteSelectedStudents()
  ├── function processBatchDelete()
  ├── function deleteOneForBatch()
  ├── function waitForBatchDelete()
  ├── function settleBatchDelete()
  ├── function handleBatchDeleteProgress()
  ├── function showBatchDeleteResults()
  ├── function updateBatchRetryAvailability()
  ├── function waitForDelete()
  ├── function settlePendingDelete()
  ├── function handleDeleteProgress()
  ├── function editSelectedStudentDetails()
  ├── function saveEditedStudentDetails()
  ├── function wipeAllFingerprints()
  ├── function wipeAllData()
  ├── function waitForWipe()
  ├── function settleWipeWait()
  ├── function handleWipeProgress()
  ├── function reenrollSelectedStudent()
  ├── function openEnrollDialog()
  ├── function validateEnrollmentFields()
  ├── function closeEnrollDialog()
  ├── function enrollPrimaryAction()
  ├── function startEnrollment()
  ├── function handleEnrollProgress()
  ├── function resetEnrollForm()
  ├── function saveEnrolledStudent()
  ├── function exportStudentsCsv()
  ├── function loadReportsPage()
  ├── function exportStatisticsReport()
  ├── function showStatisticsCharts()
  ├── function chartEmpty()
  ├── function renderStatisticsChartTab()
  ├── function renderAttendanceTimeline()
  ├── function renderSectionChart()
  ├── function renderAttendanceGradeChart()
  ├── function generateStatsReport()
  ├── function loadBackupsList()
  ├── function createBackupNow()
  ├── function restoreBackup()
  ├── function loadLogsPage()
  ├── function parseLogLine()
  ├── function applyAppLogFilter()
  ├── function clearAppLog()
  ├── function appendLiveLogLine()
  ├── function smAppend()
  ├── function _smWrite()
  ├── function toggleSerialPause()
  ├── function clearSerial()
  ├── function resetBlockReason()
  ├── function resetDevice()
  ├── function serialCmd()
  ├── function sendSerialCmd()
  ├── function updateSerialMeta()
  ├── function applyTheme()
  ├── function calendarShiftMonth()
  ├── function calendarGoToday()
  ├── function onCalendarMonthInputChange()
  ├── function loadCalendarPage()
  ├── function renderCalendarMonth()
  ├── function openCalendarEntryModal()
  ├── function closeCalendarEntryModal()
  ├── function onCalendarEntryTypeChange()
  ├── function saveCalendarEntry()
  ├── function removeCalendarEntry()
  ├── function loadSettingsPage()
  ├── function scheduleSettingsSave()
  ├── function formatDeviceStatusLines()
  ├── function refreshConnectedDevicePanel()
  ├── function refreshPortList()
  ├── function forgetSavedPort()
  ├── function populateBaudOptions()
  ├── function saveSettings()
  ├── function restoreDefaultSettings()
  ├── function openLogFolder()
  ├── function paintTitlebarRole()
  ├── function updateRole()
  ├── function tick()
  ├── function filterTable()
  └── function noteUserActivity()

python/main.py
  └── def main()

python/services/__init__.py
  └── [no class/function definitions detected]

python/services/attendance_service.py
  ├── class AttendanceService()
  ├── def get_today()
  ├── def get_paginated()
  └── def log()

python/services/student_service.py
  ├── class StudentService()
  ├── def get_all_students()
  ├── def get_student()
  ├── def save_student()
  └── def delete_student()

python/settings_store.py
  ├── def default_settings()
  ├── def load_settings()
  ├── def save_settings()
  ├── def admin_initialization_marker_exists()
  ├── def write_admin_initialization_marker()
  └── def cleanup_stale_port()

tools/_database_refactor.py
  ├── class AttendanceRow()
  ├── class StudentRow()
  ├── def get_connection()
  ├── def _row_dicts()
  ├── def init_database()
  ├── def add_student()
  ├── def update_student()
  ├── def delete_student()
  ├── def clear_all_students()
  ├── def get_student()
  ├── def get_all_students()
  ├── def get_student_count()
  ├── def register_student()
  ├── def import_students_from_list()
  ├── def log_attendance()
  ├── def get_attendance_today()
  ├── def get_attendance_all()
  ├── def get_attendance_paginated()
  ├── def get_attendance_count_today()
  ├── def get_daily_attendance_summary()
  ├── def get_attendance_by_date()
  ├── def clear_all_attendance()
  ├── def clear_all_data()
  ├── def get_attendance_by_student()
  ├── def get_students_by_grade_section()
  ├── def count_attendance_by_date()
  ├── def get_attendance_statistics()
  ├── def get_students_statistics()
  ├── def export_attendance_range()
  ├── def generate_statistics_report()
  ├── def _save_chart()
  ├── def generate_attendance_chart()
  ├── def generate_section_chart()
  ├── def generate_grade_chart()
  ├── def backup_database()
  ├── def restore_database()
  └── def list_backups()

tools/archive_unused_python.py
  └── [no class/function definitions detected]

tools/copilot_forensic_search.py
  └── [no class/function definitions detected]

tools/debug_db_connections.py
  └── def tracked_connect()

tools/runtime_manager.py
  ├── def run_process()
  ├── class RuntimeManager()
  ├── def __init__()
  ├── def refresh_ui_initial()
  ├── def append_output()
  ├── def check_environment()
  ├── def verify_dependencies()
  ├── def run_dsis()
  ├── def run_tests()
  └── def main()

tools/serial_handler_connect_probe.py
  └── [no class/function definitions detected]
```


### 2.1E Production symbols — final support tools

```text
tools/serial_pipeline_tester.py
  ├── def format_bytes()
  ├── def format_text()
  ├── def inspect_port_settings()
  ├── def capture_raw_lines()
  ├── def print_section()
  ├── def line_report()
  ├── def find_token_evidence()
  ├── def run_raw_capture()
  ├── def parse_args()
  └── def main()

tools/serial_worker_probe.py
  ├── def main()
  ├── def on_connection_changed()
  ├── def on_mode_changed()
  ├── def on_scan_event()
  ├── def on_raw_line()
  ├── def on_enroll_progress()
  ├── def on_wipe_progress()
  ├── def on_error()
  ├── def start_connect()
  ├── def stop_and_exit()
  └── def send_probe_commands()

tools/verify_gui_startup.py
  └── [no class/function definitions detected]
```

### 2.2 Tests

_Test symbol expansion follows._


### 2.2A Test/prototype symbols — UI prototypes

```text
tests/Prototype/Python/actual_ui_prototype.py
  ├── class PreviewSerialHandler()
  ├── def is_connected()
  ├── def list_available_ports()
  ├── class PreviewSerialWorker()
  ├── class ActualUIPrototypeWindow()
  ├── def __init__()
  ├── def switch_page()
  └── def main()

tests/Prototype/Python/combined_ui.py
  ├── class CombinedUIWindow()
  ├── def __init__()
  ├── def _add_navigation_icons()
  ├── def _apply_compact_icon_state()
  ├── def apply_combined_style()
  └── def main()

tests/Prototype/Python/hybrid_window.py
  ├── class HybridWindow()
  ├── def __init__()
  ├── def _build_sidebar()
  ├── def _build_header()
  ├── def _build_ui()
  ├── def _build_dashboard_page()
  ├── def _build_attendance_page()
  ├── def _build_students_page()
  ├── def _build_table_page()
  ├── def _build_reports_page()
  ├── def _build_logs_page()
  ├── def _build_settings_page()
  ├── def _select_page()
  ├── def _apply_density()
  ├── def _toggle_connection()
  ├── def _finish_scan()
  ├── def apply_hybrid_style()
  └── def main()

tests/Prototype/Python/original_window.py
  ├── class OriginalUIWindow()
  ├── def __init__()
  ├── def _build_sidebar()
  ├── def _build_header()
  ├── def _build_ui()
  ├── def _select_page()
  ├── def _select_page_identification()
  ├── def _toggle_connection()
  ├── def _apply_density()
  ├── def apply_original_style()
  └── def main()

tests/Prototype/Python/prototype_window.py
  ├── class LogoMark()
  ├── def __init__()
  ├── def paintEvent()
  ├── class PrototypeWindow()
  ├── def __init__()
  ├── def _build_ui()
  ├── def _build_sidebar()
  ├── def _build_header()
  ├── def _build_identification_page()
  ├── def _panel()
  ├── def _build_scan_panel()
  ├── def _build_details_panel()
  ├── def _build_recent_panel()
  ├── def _build_status_bar()
  ├── def _add_placeholder_page()
  ├── def _select_page()
  ├── def _set_compact()
  ├── def _apply_density()
  ├── def _update_match()
  ├── def _simulate_scan()
  ├── def _finish_scan()
  └── def main()

tests/Prototype/Python/task_manager_window.py
  ├── class TaskManagerWindow()
  ├── def __init__()
  ├── def _build_sidebar()
  ├── def _build_header()
  ├── def _apply_density()
  ├── def apply_task_manager_style()
  └── def main()

tests/Prototype/hybrid_window.py
  └── [no class/function definitions detected]

tests/Prototype/original_ui.py
  └── [no class/function definitions detected]

tests/Prototype/run_combined_ui.py
  └── [no class/function definitions detected]

tests/Prototype/run_hybrid_prototype.py
  └── [no class/function definitions detected]

tests/Prototype/run_original_ui_display.py
  └── [no class/function definitions detected]

tests/Prototype/run_qt_prototype.py
  └── [no class/function definitions detected]

tests/Prototype/run_task_manager_variant.py
  └── [no class/function definitions detected]

tests/Prototype/tests/test_actual_ui_prototype.py
  ├── class ActualUIPrototypeTest()
  ├── def setUpClass()
  ├── def test_uses_real_application_pages()
  └── def test_navigation_is_display_only()

tests/Prototype/tests/test_combined_ui.py
  ├── class CombinedUITest()
  ├── def setUpClass()
  ├── def test_combines_real_pages_with_task_manager_navigation_icons()
  └── def test_real_page_navigation_and_preview_connection_are_preserved()
```


### 2.2B Test symbols — UI prototype tests and runners

```text
tests/Prototype/tests/test_hybrid_prototype.py
  ├── class HybridPrototypeTest()
  ├── def setUpClass()
  ├── def test_hybrid_shell_has_full_app_navigation()
  └── def test_hybrid_pages_have_utility_content()

tests/Prototype/tests/test_original_ui.py
  ├── class OriginalUITest()
  ├── def setUpClass()
  ├── def test_original_shell_has_six_sections()
  ├── def test_original_shell_has_connection_and_scan_controls()
  └── def test_original_compact_sidebar_preserves_navigation()

tests/Prototype/tests/test_qt_prototype.py
  ├── class QtPrototypeTest()
  ├── def setUpClass()
  ├── def test_prototype_contains_identification_surface_and_mock_results()
  ├── def test_navigation_and_compact_density_are_interactive()
  ├── def test_selecting_result_updates_match_details()
  ├── def test_secondary_pages_have_real_prototype_controls()
  └── def test_start_scan_enters_scanning_state()

tests/Prototype/tests/test_task_manager_variant.py
  ├── class TaskManagerVariantTest()
  ├── def setUpClass()
  ├── def test_task_manager_shell_has_icon_navigation()
  ├── def test_compact_mode_keeps_icons_and_hides_labels()
  └── def test_identification_page_is_still_the_primary_workflow()

tests/app_test.py
  ├── class FingerprintApp()
  ├── def __init__()
  ├── def init_database()
  ├── def _apply_saved_settings()
  ├── def _apply_settings_to_runtime()
  ├── def save_current_settings()
  ├── def has_permission()
  ├── def update_button_permissions()
  ├── def change_role()
  ├── def _on_role_changed()
  ├── def build_ui()
  ├── def build_sidebar()
  ├── def switch_page()
  ├── def build_main_area()
  ├── def build_whs_header()
  ├── def _tick_header_clock()
  ├── def _update_header_status()
  ├── def _update_header_last_scan()
  ├── def _on_header_search()
  ├── def _on_attendance_mode_changed()
  ├── def _update_load_more_visibility()
  ├── def refresh_statistics()
  ├── def show_statistics_report()
  ├── def export_statistics_report()
  ├── def show_statistics_charts()
  ├── def toggle_connection()
  ├── def _set_connected_ui()
  ├── def refresh_serial_ports()
  ├── def open_settings_dialog()
  ├── def show_serial_help()
  ├── def auto_detect_serial_on_startup()
  ├── def try_common_serial_ports()
  ├── def _set_disconnected_ui()
  ├── def _set_reconnect_ui()
  ├── def _set_scan_mode_ui()
  ├── def _set_command_mode_ui()
  ├── def _set_enroll_mode_ui()
  ├── def _set_wipe_mode_ui()
  ├── def _clear_enroll_mode_ui()
  ├── def _parse_connection_mode()
  ├── def _schedule_attendance_refresh()
  ├── def _refresh_attendance_view_safe()
  ├── def start_scan()
  ├── def stop_scan()
  ├── def start_reader_thread()
  ├── def read_serial_output()
  ├── def enroll_sample()
  ├── def list_fingerprints()
  ├── def open_enroll_dialog()
  ├── def save_enroll_profile()
  ├── def close_enroll_dialog()
  ├── def _parse_attendance()
  ├── def _parse_enroll_progress()
  ├── def open_wipe_dialog()
  ├── def confirm_wipe()
  ├── def close_wipe_dialog()
  ├── def _parse_wipe_progress()
  ├── def open_students_list_dialog()
  ├── def close_students_dialog()
  ├── def _clear_database_data()
  ├── def refresh_student_list()
  ├── def delete_student_from_list()
  ├── def open_edit_dialog()
  ├── def backup_database()
  ├── def open_restore_dialog()
  ├── def quit_app()
  ├── def _ui_ready()
  ├── def toggle_attendance_view()
  ├── def refresh_attendance_view()
  ├── def load_more_attendance()
  ├── def _build_attendance_card()
  ├── def open_add_student_dialog()
  ├── def log_message()
  ├── def _append_log_message()
  ├── def clear_log()
  └── def main()

tests/comprehensive_test.py
  └── [no class/function definitions detected]

tests/conftest.py
  └── [no class/function definitions detected]

tests/legacy/phase2_databasev1.py
  ├── def init_database()
  ├── def add_sample_students()
  ├── def get_student()
  ├── def log_attendance()
  └── def main()

tests/legacy/phase2_databasev2.py
  ├── def init_database()
  ├── def add_sample_students()
  ├── def get_student()
  ├── def log_attendance()
  ├── def read_line()
  ├── def parse_scan()
  └── def main()

tests/legacy/phase2_databasev3.py
  ├── def init_database()
  ├── def add_sample_students()
  ├── def get_student()
  ├── def log_attendance()
  ├── def should_ignore()
  ├── def send_command()
  ├── def input_thread()
  └── def main()

tests/legacy/phase2_databasev4.py
  ├── def init_database()
  ├── def add_sample_students()
  ├── def log_attendance()
  ├── def should_ignore()
  ├── def send_command()
  ├── def input_thread()
  └── def main()

tests/legacy/phase2_serial_test.py
  └── def main()

tests/manual_hardware_scripts/test_debug_raw_lines.py
  ├── def debug_raw_lines()
  └── def track_raw_line()

tests/manual_hardware_scripts/test_enrollment_with_worker.py
  ├── def simulate_enrollment_with_worker()
  └── def track_progress()

tests/manual_hardware_scripts/test_gui_demo.py
  ├── class AttendanceTestGUI()
  ├── def __init__()
  ├── def build_sidebar()
  ├── def build_top_bar()
  ├── def build_main_content()
  ├── def on_setting_changed()
  ├── def save_settings()
  └── def log_message()
```


### 2.2C Test symbols — core test suite A

```text
tests/manual_hardware_scripts/test_minimal_enroll.py
  └── def minimal_enroll_test()

tests/physical_esp32_smoke.py
  ├── def _connect_hardware()
  ├── def _collect_lines()
  ├── def test_physical_esp32_v3_safe_lifecycle()
  └── def test_physical_esp32_empty_device_wipe_and_absent_delete()

tests/qt_gui_interactive.py
  └── def _runtime_root()

tests/test_active_firmware_protocol.py
  └── def test_firmware_destructive_commands_require_host_connection()

tests/test_attendance_export_rows.py
  ├── def test_export_rows_leave_time_out_empty_for_single_time_in()
  └── def test_export_rows_separate_time_in_and_time_out()

tests/test_attendance_parsing.py
  ├── class AttendanceParsingTest()
  └── def test_registered_scan_is_logged_without_shadowing_error()

tests/test_attendance_processor.py
  ├── class AttendanceProcessorTests()
  ├── def test_process_registered_scan_and_cooldown()
  ├── def fake_log_attendance()
  ├── def test_process_unknown_scan_and_cooldown()
  ├── def fake_log_attendance()
  ├── def test_unreadable_card_preserves_firmware_reason()
  ├── def test_card_payload_must_match_linked_student_and_uid()
  ├── def test_process_json_attendance_match()
  ├── def fake_log_attendance()
  ├── def test_process_json_attendance_match_with_bom_and_whitespace()
  ├── def fake_log_attendance()
  ├── def test_reset_clears_state()
  ├── def fake_log_attendance()
  ├── def test_card_match_uses_card_uid_resolution()
  ├── def fake_log_attendance()
  ├── def test_unknown_card_is_logged_as_unknown_without_crashing()
  ├── def fake_log_attendance()
  ├── def test_card_event_accepts_data_hex_payload()
  ├── def test_active_rfid_register_session_skips_attendance_logging()
  ├── def test_rfid_registration_commits_only_after_matching_verified_write()
  ├── def test_failed_rfid_write_preserves_existing_link()
  ├── def test_rfid_registration_is_rejected_while_attendance_scan_is_active()
  ├── def test_batch_rfid_erase_arms_one_tap_erase_without_attendance_logging()
  ├── def test_batch_rfid_erase_does_not_unlink_without_verified_zero_readback()
  ├── def test_batch_rfid_erase_requires_uid_even_when_payload_is_verified()
  ├── def test_batch_rfid_erase_rejects_nonzero_readback()
  ├── def test_batch_rfid_erase_unlinks_after_verified_zero_readback()
  ├── def test_invalid_card_payload_is_unknown_even_when_uid_is_linked()
  ├── def fake_log_attendance()
  ├── def test_bind_student_card_rejects_claimed_uid()
  ├── def test_rfid_payload_round_trip_uses_app_key()
  ├── def test_rfid_payload_tampering_and_overflow_fail_closed()
  ├── def test_rfid_payload_wrong_key_fails_closed()
  ├── def test_new_rfid_key_is_separate_from_legacy_xor_keys()
  └── def test_cmd_card_write_hex_uses_hex_payload_safe_format()

tests/test_attendance_refresh.py
  ├── def test_schedule_attendance_refresh_uses_main_thread_callback()
  └── def fake_after()

tests/test_attendance_status.py
  ├── def test_time_in_status_boundaries()
  ├── def test_time_out_status_boundaries()
  ├── def test_zero_absent_threshold_keeps_late_status()
  ├── def test_half_day_schedule_is_used_for_time_out()
  └── def test_invalid_half_day_schedule_is_rejected()

tests/test_attendance_ui_regressions.py
  ├── def test_start_scan_resets_mode_state()
  └── def test_get_attendance_today_orders_newest_first()

tests/test_attendance_ui_utils.py
  ├── def test_format_attendance_display_uses_student_name_when_present()
  └── def test_format_attendance_display_falls_back_to_id_when_name_missing()

tests/test_auto_port_probe.py
  ├── class DummyVar()
  ├── def __init__()
  ├── def get()
  ├── def set()
  ├── class DummyComboBox()
  ├── def configure()
  ├── class DummySerialHandler()
  ├── def __init__()
  ├── def list_available_ports()
  ├── def test_common_port_candidates_include_common_values()
  ├── def test_refresh_serial_ports_initial_does_not_trigger_auto_detect_again()
  └── def fail_auto_detect()

tests/test_bfeas_app2_import.py
  └── def test_bfeas_app2_script_runs_without_module_path_errors()

tests/test_button_in_context.py
  └── def test_button_click_in_studentpage()

tests/test_database_features.py
  ├── class DatabaseFeaturesTest()
  └── def test_clear_all_students_removes_all_profiles()
```


### 2.2D Test symbols — core test suite B

```text
tests/test_database_reset.py
  └── def test_clear_all_data_clears_students_and_attendance()

tests/test_database_security.py
  ├── class TestRestoreDatabasePathTraversal()
  ├── def test_connection_enables_wal_and_busy_timeout()
  ├── def test_restore_database_rejects_paths_outside_backups_dir()
  ├── def test_restore_database_rejects_absolute_paths_outside_backups()
  ├── def test_restore_database_accepts_valid_backup_in_backups_dir()
  ├── def test_restore_database_rejects_nonexistent_files()
  ├── def test_restore_database_rejects_wrong_file_type()
  ├── def test_restore_database_rejects_tampered_db_file_with_invalid_sqlite_header()
  ├── def test_restore_database_sanitizes_error_messages()
  ├── def test_restore_database_rejects_sibling_directory_with_similar_name()
  ├── def test_restore_database_accepts_nested_backup_subdirectory()
  ├── class TestClearAllDataAuthorizationBoundary()
  ├── def test_clear_all_data_blocked_for_role_without_wipe_permission()
  ├── def test_clear_all_data_blocked_for_unknown_role()
  ├── def test_clear_all_data_succeeds_for_admin_role()
  ├── def test_clear_all_data_cannot_be_bypassed_by_calling_it_directly()
  ├── class TestDeleteStudentAuthorizationBoundary()
  ├── def test_delete_student_blocked_for_role_without_delete_permission()
  ├── def test_delete_student_blocked_when_device_not_connected()
  └── def test_delete_student_succeeds_for_admin_role()

tests/test_dialog_enrollment_integration.py
  ├── def _any_serial_port_present()
  ├── def _skip_or_fail()
  ├── def test_enrollment_dialog_in_gui()
  ├── def track_enroll_progress()
  └── def auto_enroll()

tests/test_dialog_handlers.py
  ├── def test_wipe_dialog_uses_real_confirmation_flow()
  └── def fake_cmd_wipe()

tests/test_enrollment_debug.py
  └── def test_enrollment_flow()

tests/test_enrollment_dialog_ux.py
  ├── def qapp()
  ├── def setup_database()
  ├── def mock_serial_handler()
  ├── def mock_serial_worker()
  ├── def enroll_dialog()
  ├── class TestEnrollDialogInitialState()
  ├── def test_dialog_opens_with_initial_state()
  ├── def test_start_enrollment_button_disabled_on_open()
  ├── def test_button_text_is_start_enrollment_initially()
  ├── def test_assigned_id_shows_pending()
  ├── def test_all_form_fields_empty_initially()
  ├── class TestEnrollDialogFormValidation()
  ├── def test_incomplete_form_keeps_button_disabled()
  ├── def test_invalid_student_no_keeps_button_disabled()
  ├── def test_invalid_name_keeps_button_disabled()
  ├── def test_valid_form_enables_button()
  ├── def test_valid_form_with_special_names()
  ├── def test_clearing_field_disables_button()
  ├── class TestEnrollDialogEnrollingState()
  ├── def test_clicking_start_transitions_to_enrolling()
  ├── def test_enrolling_disables_button()
  ├── def test_enrolling_changes_button_text()
  ├── def test_prevent_duplicate_enrollments()
  ├── def test_disconnect_not_connected_shows_warning()
  ├── class TestEnrollDialogEnrollmentSuccess()
  ├── def test_success_event_transitions_to_success_state()
  ├── def test_success_updates_assigned_id()
  ├── def test_success_changes_button_to_save()
  ├── def test_success_enables_save_button()
  ├── def test_cancelled_event_returns_to_initial_state()
  ├── def test_cancelled_re_enables_button_if_form_valid()
  ├── def test_error_event_returns_to_initial_state()
  ├── class TestEnrollDialogSaving()
  ├── def test_save_without_fingerprint_shows_warning()
  ├── def test_save_with_valid_data_calls_service()
  ├── def test_save_transitions_to_saving_state()
  ├── def test_save_disables_button_during_save()
  ├── def test_prevent_duplicate_saves()
  ├── def test_save_failure_returns_to_success_state()
  ├── class TestEnrollDialogCancel()
  ├── def test_cancel_button_closes_dialog()
  ├── def test_cancel_stops_enrollment_if_in_progress()
  ├── def test_cancel_deletes_stored_fingerprint_before_student_save()
  └── def test_cancel_disconnects_signals()

tests/test_error_message_sanitization.py
  ├── class TestReportGenerationErrorSanitization()
  ├── def test_generate_statistics_report_hides_raw_exception_on_failure()
  ├── class _BoomConnection()
  ├── def execute()
  ├── def close()
  ├── class TestBackupErrorSanitization()
  ├── def test_backup_database_hides_raw_exception_on_failure()
  ├── class TestStudentSaveErrorSanitization()
  ├── def test_add_student_generic_integrity_error_is_sanitized()
  ├── class _BoomConnection()
  ├── def execute()
  ├── def commit()
  ├── def close()
  ├── def test_add_student_known_constraint_still_gets_friendly_message()
  ├── def test_update_student_generic_integrity_error_is_sanitized()
  ├── class _BoomConnection()
  ├── def execute()
  ├── def commit()
  └── def close()

tests/test_firmware_helper.py
  └── def test_discover_firmware_candidates_prefers_bin()

tests/test_gui_settings_integration.py
  ├── def test_app_applies_auto_reconnect_setting()
  ├── def test_app_applies_auto_detect_serial_setting()
  ├── def test_app_applies_profiler_setting()
  ├── def test_compact_sidebar_toggle_changes_button_display()
  ├── def get_display_text()
  ├── def test_settings_change_persists_after_reload()
  ├── def test_all_toggles_have_runtime_effect()
  └── def test_saved_role_persists_in_settings_payload()

tests/test_gui_shutdown.py
  ├── def create_app_or_skip()
  ├── class GuiShutdownTest()
  ├── def test_quit_app_marks_shutdown_and_closes_window()
  └── def test_append_log_message_after_destroy_is_safe()

tests/test_gui_web_smoke.py
  ├── def test_v3_web_shell_contains_all_primary_workflows()
  ├── def test_unknown_attendance_rows_use_unknown_data_label()
  ├── def test_rfid_registration_waits_for_verified_write_result()
  ├── def test_student_refresh_preserves_the_selected_fingerprint()
  ├── def test_v3_validation_api_returns_field_feedback()
  ├── class Result()
  ├── def __init__()
  ├── def test_v3_statistics_report_includes_students_without_attendance()
  ├── def test_v3_serial_troubleshooting_message_uses_detected_ports()
  ├── def test_v3_profiler_collects_and_reports_enabled_measurements()
  ├── def test_v3_profiler_is_inert_when_disabled()
  ├── def test_v3_web_bundle_uses_native_unicode_display_values()
  ├── def test_v3_student_detail_returns_today_attendance_status()
  ├── def test_v3_student_detail_without_scan_is_absent()
  ├── def test_v3_push_json_round_trips_unicode_names()
  ├── def test_v3_student_csv_round_trips_unicode()
  ├── def test_v3_csv_preserves_long_student_numbers_and_attendance_status()
  ├── def test_v3_today_export_uses_visible_fallback_rows()
  ├── def test_v3_csv_export_cancel_does_not_write_to_default_folder()
  ├── def test_v3_csv_save_dialog_uses_pywebview_save_contract()
  ├── def test_v3_all_students_export_includes_attendance_columns()
  ├── def test_v3_all_students_export_uses_attendance_date()
  ├── def test_v3_attendance_page_uses_date_specific_schedule()
  ├── def test_v3_global_schedule_rejects_time_out_before_time_in()
  ├── def test_v3_calendar_bulk_half_day_uses_valid_times()
  ├── def fake_load_settings()
  ├── def fake_save_settings()
  ├── def test_v3_attendance_evaluation_ignores_weekend_activity()
  ├── def test_v3_recent_export_uses_visible_page()
  ├── def test_v3_weekly_export_uses_seven_day_date_range()
  ├── def export_range()
  ├── def test_v3_weekly_export_uses_selected_calendar_week()
  ├── def export_range()
  ├── def test_restore_publishes_v3_data_refresh_event()
  └── def test_v3_styles_define_narrow_window_layout_rules()

tests/test_mode_exclusivity.py
  ├── class ModeExclusivityTest()
  ├── def setUp()
  ├── def test_cannot_start_scan_during_wipe()
  ├── def test_cannot_enroll_during_wipe()
  └── def test_wipe_dialog_sets_and_clears_wipe_mode()

tests/test_permissions_and_attendance_tagging.py
  ├── def temp_db()
  ├── class TestBackendPermissionEnforcement()
  ├── def test_guest_cannot_enroll()
  ├── def test_guest_cannot_delete()
  ├── def test_teacher_cannot_wipe()
  ├── def test_admin_can_wipe()
  ├── def test_unknown_role_is_denied_not_allowed()
  ├── def test_disconnect_cancels_active_device_state_before_closing_port()
  ├── def test_connected_delete_student_requires_device_confirmation()
  ├── def test_scan_state_machine_updates_mode_and_scanning_flags()
  ├── def test_unexpected_disconnect_clears_pending_operations_and_publishes_state()
  ├── def test_disconnect_clears_pending_delete_before_future_operations()
  ├── def test_device_operations_are_mutually_exclusive()
  ├── def test_connect_honors_explicit_auto_detect_setting()
  ├── def test_guest_cannot_list_backups()
  ├── def test_guest_cannot_generate_statistics_report()
  ├── def test_enrollment_instructions_are_pushed_as_step_events()
  ├── def test_discard_enrollment_removes_unsaved_device_template()
  ├── def test_commands_help_action_sends_intentional_unknown_command()
  ├── def test_wipe_all_data_clears_local_database_without_device_command()
  ├── def test_confirmed_device_wipe_clears_linked_local_data()
  ├── class TestAttendanceEventTypeTagging()
  ├── def test_first_scan_of_day_is_tagged_time_in()
  ├── def test_second_scan_same_day_is_tagged_time_out()
  ├── def test_reenrollment_migrates_existing_student_without_duplicate_number()
  ├── def test_delete_student_preserves_attendance_as_unregistered()
  ├── def test_daily_summary_uses_tagged_time_in_and_out()
  ├── def test_migration_backfills_legacy_rows_without_event_type()
  ├── class TestTodayAttendanceFallbackFlag()
  ├── def test_api_does_not_start_backup_thread_until_window_is_attached()
  ├── def test_is_fallback_false_when_todays_records_exist()
  ├── def test_is_fallback_true_when_only_older_records_exist()
  └── def test_get_attendance_today_still_returns_plain_list()

tests/test_project_structure.py
  ├── class ProjectStructureTests()
  └── def test_core_modules_import()

tests/test_qt_attendance_page.py
  ├── class QtAttendancePageTest()
  ├── def setUpClass()
  ├── def setUp()
  └── def test_empty_state_message_is_shown_when_no_records_exist()
```


### 2.2E Test symbols — core test suite C

```text
tests/test_qt_enrollment_flow.py
  ├── class TestQtEnrollmentFlow()
  ├── def setUpClass()
  ├── def setUp()
  ├── def tearDown()
  ├── def test_save_student_and_retrieve()
  ├── def test_multiple_enrollments()
  ├── def test_duplicate_fingerprint_id_updates_existing()
  └── def test_enrollment_to_table_refresh()

tests/test_qt_main_window.py
  ├── class QtMainWindowScanTests()
  ├── def setUpClass()
  └── def test_scan_is_blocked_when_enrollment_dialog_is_active()

tests/test_qt_serial_worker.py
  ├── class TestSerialWorkerMessageParsing()
  ├── def setUpClass()
  ├── def setUp()
  ├── def test_enrollment_message_parsing()
  ├── def test_wipe_progress_message_parsing()
  ├── def test_mode_line_parsing()
  ├── def test_json_mode_line_parsing()
  ├── def test_enrollment_success_flow()
  └── def test_regex_patterns_consistency()

tests/test_qt_settings_logs.py
  ├── class QtSettingsLogsTest()
  ├── def setUpClass()
  ├── def test_logs_page_clear_restores_ready_message()
  └── def test_settings_page_initializes_with_serial_handler()

tests/test_qt_shell.py
  ├── class QtShellTest()
  ├── def setUpClass()
  ├── def test_sidebar_contains_expected_navigation_items()
  ├── def test_main_window_constructs_with_pages()
  ├── def test_dashboard_page_displays_recent_activity_section()
  └── def test_reports_page_displays_summary_label()

tests/test_qt_students_page.py
  ├── class QtStudentsPageTest()
  ├── def setUpClass()
  ├── def setUp()
  ├── def test_save_student_details_persists_student_and_refreshes_table()
  ├── def test_unicode_name_persists_and_appears_in_qt_reports()
  ├── def test_delete_blocked_shows_message_without_crashing_or_deleting()
  ├── def delete_from_db()
  ├── def test_delete_succeeds_for_authorized_role()
  ├── def delete_from_db()
  ├── def test_delete_disabled_while_disconnected()
  └── class _FakeDeleteWorker()

tests/test_qt_thread_exception_handling.py
  ├── def test_handle_thread_exception_without_thread()
  └── def fake_exception()

tests/test_reports_page_import.py
  └── def test_reports_page_can_import_database_helper()

tests/test_responsive_layout.py
  ├── def test_resolve_window_size_uses_screen_bounds()
  ├── def test_resolve_dialog_size_stays_within_screen()
  ├── def test_sidebar_width_scales_for_small_screens()
  └── def test_scale_value_clamps_to_bounds()

tests/test_sensor_failure_handshake_recovery.py
  ├── class FakeSerialWithBootTiming()
  ├── def __init__()
  ├── def open()
  ├── def in_waiting()
  ├── def write()
  ├── def flush()
  ├── def reset_output_buffer()
  ├── def readline()
  ├── def close()
  ├── def fake_serial_module()
  ├── def _install()
  ├── def _make_serial()
  ├── def test_connects_despite_sensor_failure_hang()
  ├── def test_still_recognizes_healthy_boot_sequence_from_boot_phase()
  └── def test_falls_back_to_id_probe_when_nothing_arrives_during_boot()

tests/test_serial_handler_host_gate.py
  └── def test_adopted_serial_connection_notifies_firmware_host_connected()

tests/test_serial_monitor_boot_banner.py
  ├── class FakeSerial()
  ├── def __init__()
  ├── def open()
  ├── def in_waiting()
  ├── def write()
  ├── def flush()
  ├── def reset_output_buffer()
  ├── def readline()
  ├── def close()
  ├── def fake_serial_module()
  ├── def test_probe_captures_full_boot_banner_not_just_identity_json()
  └── def test_probe_stops_promptly_once_ready_status_seen()

tests/test_serial_troubleshooting.py
  └── def test_troubleshooting_message_mentions_common_drivers_and_steps()

tests/test_settings_persistence.py
  ├── def test_settings_round_trip()
  └── def test_load_settings_merges_with_defaults()

tests/test_settings_toggles.py
  ├── def test_default_settings()
  ├── def test_save_and_load_settings()
  ├── def test_settings_toggle_persistence()
  ├── def test_settings_json_format()
  ├── def test_toggle_types()
  └── def test_settings_merge_on_load()
```


### 2.2F Test symbols — final test files

```text
tests/test_student_input_regression.py
  ├── class TestStudentInputValidationRegressions()
  ├── def test_name_with_comma_and_period()
  ├── def test_name_with_multiple_commas()
  ├── def test_name_with_apostrophe_and_comma()
  ├── def test_name_with_unicode_letters()
  ├── def test_unicode_names_round_trip_in_validation_feedback()
  ├── def test_section_with_hyphens()
  ├── def test_student_no_with_special_chars()
  ├── def test_reject_control_characters()
  ├── def test_reject_excessive_length()
  ├── def test_reject_null_bytes()
  ├── def test_empty_name_rejected()
  ├── def test_whitespace_only_name_rejected()
  ├── def test_live_validation_feedback_preserves_valid_name()
  ├── def test_live_validation_feedback_reports_unsupported_character()
  ├── def test_live_validation_feedback_accepts_section_formats()
  └── def test_complex_real_world_names()

tests/test_student_input_validation.py
  ├── class TestStudentInputValidation()
  ├── def setup()
  ├── def test_validate_fingerprint_id_too_low()
  ├── def test_validate_fingerprint_id_too_high()
  ├── def test_validate_fingerprint_id_valid()
  ├── def test_validate_student_no_empty()
  ├── def test_validate_student_no_too_long()
  ├── def test_validate_student_no_valid()
  ├── def test_validate_student_no_invalid_chars()
  ├── def test_validate_student_name_empty()
  ├── def test_validate_student_name_too_long()
  ├── def test_validate_student_name_valid()
  ├── def test_validate_student_name_invalid_chars()
  ├── def test_validate_grade_empty()
  ├── def test_validate_grade_valid()
  ├── def test_validate_section_empty()
  ├── def test_validate_section_valid()
  ├── def test_add_student_with_invalid_input()
  ├── def test_add_student_with_valid_input()
  └── def test_update_student_with_invalid_input()

tests/test_theme_switching.py
  ├── class DummyApp()
  ├── def __init__()
  ├── def after()
  ├── def winfo_exists()
  ├── def update_idletasks()
  ├── def test_apply_appearance_mode_schedules_safe_theme_change()
  ├── def fake_set_appearance_mode()
  └── def test_get_theme_colors_returns_mode_specific_values()

tests/test_type_hints.py
  └── def test_core_database_and_serial_helpers_have_type_hints()

tests/test_v3_authentication.py
  ├── def test_password_hash_is_salted_and_verifies()
  ├── def test_role_hierarchy_is_ordered()
  ├── def test_all_roles_can_access_attendance_evaluation()
  ├── def test_api_starts_guest_and_requires_password_for_elevation()
  ├── def test_guest_cannot_elevate_to_teacher_without_password()
  ├── def test_admin_can_switch_down_to_teacher_without_password()
  ├── def test_teacher_to_admin_requires_password_without_changing_role()
  ├── def test_admin_to_admin_does_not_require_password()
  ├── def test_guest_can_elevate_to_admin_with_correct_password()
  ├── def test_wrong_password_does_not_elevate()
  ├── def test_admin_password_lockout_after_repeated_failures()
  ├── def test_first_run_recovery_refuses_password_creation_when_marker_exists()
  ├── def test_admin_initialization_marker_round_trip()
  ├── def test_guest_record_reads_are_restricted()
  ├── def test_lock_and_expiry_return_to_guest()
  └── def test_guest_settings_update_is_rejected()

tests/test_vidpid_normalization.py
  ├── class TestVidPidNormalization()
  ├── def test_get_default_com_port_prefers_known_vidpid()
  └── def test_device_discovery_score_recognizes_vidpid()

tests/whs_dashboard.py
  ├── def make_circle_avatar()
  ├── class RoundedCard()
  ├── def __init__()
  ├── class WHSDashboard()
  ├── def __init__()
  ├── def _avatar()
  ├── def _build_sidebar()
  ├── def _build_main()
  ├── def _tick_clock()
  ├── def _pill()
  ├── def _build_attendance_table()
  ├── def _build_abnormal_records()
  ├── def _build_need_work_form()
  ├── def _build_system_status()
  └── def info_row()
```

### 2.3 Archive / historical source

_Archive files are retained in the complete repository tree. Their symbols are historical/reference code rather than part of the maintained V3 runtime._


### 2.3A Archive symbols — diagnostics and early GUI redesign

```text
archive/diagnostics/discovery_handshake_probe.py
  ├── def list_available_ports()
  ├── def parse_expected_handshake()
  ├── def probe_port()
  └── def main()

archive/diagnostics/serial_monitor_test.py
  ├── class SerialMonitor()
  ├── def __init__()
  ├── def open()
  ├── def close()
  ├── def _reader_loop()
  ├── def _report_disconnection()
  ├── def start_input_loop()
  ├── def _input_loop()
  ├── def send_command()
  ├── def wait_for_first_byte()
  ├── def get_summary()
  ├── def parse_args()
  ├── def print_status()
  ├── def automated_test()
  └── def main()

archive/diagnostics/serial_pipeline_tester.py
  ├── def list_ports_available()
  ├── def print_bytes()
  ├── def open_serial()
  ├── def capture_port()
  ├── def replay_file()
  └── def main()

archive/diagnostics/temp_serial_port_info.py
  └── [no class/function definitions detected]

archive/diagnostics/tmp_serial_dtr_test.py
  └── [no class/function definitions detected]

archive/diagnostics/tmp_serial_handler_probe.py
  └── [no class/function definitions detected]

archive/diagnostics/tmp_serial_probe.py
  └── [no class/function definitions detected]

archive/legacy-ui/gui_qt_redesign/gui_qt/__init__.py
  └── [no class/function definitions detected]

archive/legacy-ui/gui_qt_redesign/gui_qt/main_qt.py
  ├── def load_stylesheet()
  └── def main()

archive/legacy-ui/gui_qt_redesign/gui_qt/main_window.py
  ├── class MainWindow()
  ├── def __init__()
  ├── def switch_page()
  ├── def on_connection_changed()
  ├── def on_scan_event()
  ├── def on_serial_error()
  └── def closeEvent()

archive/legacy-ui/gui_qt_redesign/gui_qt/pages/__init__.py
  └── [no class/function definitions detected]

archive/legacy-ui/gui_qt_redesign/gui_qt/pages/attendance_page.py
  ├── class AttendancePage()
  ├── def __init__()
  ├── def refresh()
  ├── def _populate()
  └── def on_scan_event()

archive/legacy-ui/gui_qt_redesign/gui_qt/pages/dashboard_page.py
  ├── class DashboardPage()
  ├── def __init__()
  ├── def refresh()
  └── def on_scan_event()
```


### 2.3B Archive symbols — GUI redesign continuation

```text
archive/legacy-ui/gui_qt_redesign/gui_qt/pages/logs_page.py
  ├── class LogsPage()
  ├── def __init__()
  └── def append_line()

archive/legacy-ui/gui_qt_redesign/gui_qt/pages/reports_page.py
  ├── class ReportsPage()
  ├── def __init__()
  └── def on_export_clicked()

archive/legacy-ui/gui_qt_redesign/gui_qt/pages/settings_page.py
  ├── class SettingsPage()
  ├── def __init__()
  └── def on_upload_firmware()

archive/legacy-ui/gui_qt_redesign/gui_qt/pages/students_page.py
  ├── class StudentsPage()
  ├── def __init__()
  ├── def refresh()
  ├── def on_enroll_clicked()
  └── def on_delete_clicked()

archive/legacy-ui/gui_qt_redesign/gui_qt/widgets/__init__.py
  └── [no class/function definitions detected]

archive/legacy-ui/gui_qt_redesign/gui_qt/widgets/sidebar.py
  ├── class Sidebar()
  └── def __init__()

archive/legacy-ui/gui_qt_redesign/gui_qt/widgets/stat_card.py
  ├── class StatCard()
  ├── def __init__()
  └── def set_value()

archive/legacy-ui/gui_qt_redesign/gui_qt/workers/__init__.py
  └── [no class/function definitions detected]

archive/legacy-ui/gui_qt_redesign/gui_qt/workers/serial_worker.py
  ├── class SerialWorker()
  ├── def __init__()
  ├── def run()
  ├── def _read_loop()
  ├── def stop()
  ├── def _connect_stub()
  ├── def _read_line_stub()
  └── def _parse_stub()

archive/legacy-ui/gui_qt_redesign_2/gui_qt/__init__.py
  └── [no class/function definitions detected]

archive/legacy-ui/gui_qt_redesign_2/gui_qt/main_qt.py
  ├── def load_stylesheet()
  └── def main()

archive/legacy-ui/gui_qt_redesign_2/gui_qt/main_window.py
  ├── class MainWindow()
  ├── def __init__()
  ├── def switch_page()
  ├── def on_connect_clicked()
  ├── def on_connection_settings_changed()
  ├── def on_connection_changed()
  ├── def on_scan_event()
  ├── def on_serial_error()
  └── def closeEvent()

archive/legacy-ui/gui_qt_redesign_2/gui_qt/pages/__init__.py
  └── [no class/function definitions detected]
```


### 2.3C Archive symbols — V1/V2 GUI branches

```text
archive/legacy-ui/gui_qt_redesign_2/gui_qt/pages/attendance_page.py
  ├── class AttendancePage()
  ├── def __init__()
  ├── def refresh()
  ├── def _populate()
  └── def on_scan_event()

archive/legacy-ui/gui_qt_redesign_2/gui_qt/pages/dashboard_page.py
  ├── class DashboardPage()
  ├── def __init__()
  ├── def refresh()
  └── def on_scan_event()

archive/legacy-ui/gui_qt_redesign_2/gui_qt/pages/logs_page.py
  ├── class LogsPage()
  ├── def __init__()
  ├── def append_line()
  └── def clear()

archive/legacy-ui/gui_qt_redesign_2/gui_qt/pages/reports_page.py
  ├── class ReportsPage()
  ├── def __init__()
  ├── def refresh()
  ├── def on_export_clicked()
  ├── def on_backup_clicked()
  └── def on_restore_clicked()

archive/legacy-ui/gui_qt_redesign_2/gui_qt/pages/settings_page.py
  ├── class SettingsPage()
  ├── def __init__()
  ├── def _populate_ports()
  ├── def _refresh_firmware_status()
  ├── def on_upload_firmware()
  ├── def progress()
  ├── def run_upload()
  └── def on_save()

archive/legacy-ui/gui_qt_redesign_2/gui_qt/pages/students_page.py
  ├── class EnrollDialog()
  ├── def __init__()
  ├── def on_start()
  ├── def on_enroll_progress()
  ├── def accept()
  ├── def get_values()
  ├── def closeEvent()
  ├── class WipeDialog()
  ├── def __init__()
  ├── def on_confirm()
  ├── def on_wipe_progress()
  ├── def closeEvent()
  ├── class StudentsPage()
  ├── def __init__()
  ├── def refresh()
  ├── def on_enroll_clicked()
  ├── def on_delete_clicked()
  └── def on_wipe_clicked()

archive/legacy-ui/gui_qt_redesign_2/gui_qt/widgets/__init__.py
  └── [no class/function definitions detected]

archive/legacy-ui/gui_qt_redesign_2/gui_qt/widgets/sidebar.py
  ├── class Sidebar()
  └── def __init__()

archive/legacy-ui/gui_qt_redesign_2/gui_qt/widgets/stat_card.py
  ├── class StatCard()
  ├── def __init__()
  └── def set_value()

archive/legacy-ui/gui_qt_redesign_2/gui_qt/workers/__init__.py
  └── [no class/function definitions detected]

archive/legacy-ui/gui_qt_redesign_2/gui_qt/workers/serial_worker.py
  ├── class SerialWorker()
  ├── def __init__()
  ├── def run()
  ├── def _process_line()
  ├── def _parse_enroll_progress()
  ├── def _parse_wipe_progress()
  └── def stop()

archive/legacy-ui/testing_area/core/database_addition_snippet.py
  └── def get_daily_attendance_summary()

archive/legacy-ui/testing_area/gui/legacy/app_test.py
  └── [no class/function definitions detected]
```


### 2.3D Archive symbols — V1/V2 source continuation

```text
archive/legacy-ui/testing_area/gui/legacy/app_test1.py
  ├── def make_circle_avatar()
  ├── class FingerprintApp()
  ├── def __init__()
  ├── def init_database()
  ├── def _apply_saved_settings()
  ├── def _apply_settings_to_runtime()
  ├── def save_current_settings()
  ├── def has_permission()
  ├── def update_button_permissions()
  ├── def change_role()
  ├── def _on_role_changed()
  ├── def build_ui()
  ├── def switch_page()
  ├── def build_sidebar()
  ├── def action_btn()
  ├── def _avatar()
  ├── def refresh_student_roster()
  ├── def build_main_area()
  ├── def _safe_build_page_tab()
  ├── def build_dashboard_tab()
  ├── def _compute_month_attendance_grid()
  ├── def _build_work_attendance_card()
  ├── def _get_abnormal_records()
  ├── def _build_abnormal_records_card()
  ├── def _build_need_work_panel()
  ├── def _on_quick_enroll_submit()
  ├── def build_system_status_panel()
  ├── def refresh_dashboard_tab()
  ├── def _status_row()
  ├── def _info_row()
  ├── def build_whs_header()
  ├── def _tick_header_clock()
  ├── def _update_header_status()
  ├── def _update_header_last_scan()
  ├── def _on_header_search()
  ├── def _on_attendance_mode_changed()
  ├── def _update_load_more_visibility()
  ├── def refresh_statistics()
  ├── def show_statistics_report()
  ├── def export_statistics_report()
  ├── def show_statistics_charts()
  ├── def toggle_connection()
  ├── def _set_connected_ui()
  ├── def refresh_serial_ports()
  ├── def open_settings_dialog()
  ├── def show_serial_help()
  ├── def auto_detect_serial_on_startup()
  ├── def try_common_serial_ports()
  ├── def _set_disconnected_ui()
  ├── def _set_reconnect_ui()
  ├── def _set_scan_mode_ui()
  ├── def _set_command_mode_ui()
  ├── def _set_enroll_mode_ui()
  ├── def _set_wipe_mode_ui()
  ├── def _clear_enroll_mode_ui()
  ├── def _parse_connection_mode()
  ├── def _schedule_attendance_refresh()
  ├── def _refresh_attendance_view_safe()
  ├── def start_scan()
  ├── def stop_scan()
  ├── def start_reader_thread()
  ├── def read_serial_output()
  ├── def enroll_sample()
  ├── def list_fingerprints()
  ├── def open_enroll_dialog()
  ├── def save_enroll_profile()
  ├── def close_enroll_dialog()
  ├── def _parse_attendance()
  ├── def _parse_enroll_progress()
  ├── def open_wipe_dialog()
  ├── def confirm_wipe()
  ├── def close_wipe_dialog()
  ├── def _parse_wipe_progress()
  ├── def open_students_list_dialog()
  ├── def close_students_dialog()
  ├── def _clear_database_data()
  ├── def refresh_student_list()
  ├── def delete_student_from_list()
  ├── def open_edit_dialog()
  ├── def backup_database()
  ├── def open_restore_dialog()
  ├── def quit_app()
  ├── def _ui_ready()
  ├── def toggle_attendance_view()
  ├── def refresh_attendance_view()
  ├── def load_more_attendance()
  ├── def _build_attendance_card()
  ├── def open_add_student_dialog()
  ├── def log_message()
  ├── def _append_log_message()
  ├── def clear_log()
  └── def main()

archive/legacy-ui/testing_area/gui/legacy/bfeas_app.py
  ├── class BFEASApp()
  ├── def __init__()
  ├── def _build_topbar()
  ├── def _build_sidebar()
  ├── def _section_label()
  ├── def _nav_button()
  ├── def _build_main()
  ├── def _populate_table()
  ├── def _update_showing_label()
  ├── def _filter_table()
  └── def _on_view_reports()

archive/legacy-ui/testing_area/gui/legacy/bfeas_app2.py
  ├── class AttendanceReportPage()
  ├── def __init__()
  ├── def build()
  ├── def refresh()
  ├── def _valid_date()
  ├── def _apply_search()
  ├── def _render_page()
  ├── def _prev_page()
  ├── def _next_page()
  ├── def export_to_excel()
  ├── def build_reports_tab()
  ├── class BFEASApp2()
  ├── def __init__()
  ├── def _build_topbar()
  ├── def _build_sidebar()
  ├── def _section_label()
  ├── def _nav_button()
  ├── def _build_main_content()
  ├── def log_message()
  └── def main()

archive/legacy-ui/testing_area/gui/legacy/reports_table_page.py
  ├── def _day_name()
  ├── class ReportsPage()
  ├── def __init__()
  ├── def build()
  ├── def _style_treeview()
  ├── def apply_date_filter()
  ├── def on_entries_changed()
  ├── def on_search_changed()
  ├── def sort_by()
  ├── def change_page()
  ├── def _recompute_and_render()
  ├── def matches()
  ├── def _render_page()
  ├── def open_add_dialog()
  └── def save()

archive/legacy-ui/testing_area/services/backup.py
  └── def backup_database()

archive/legacy-ui/testing_area/services/excel_export.py
  ├── def _style_sheet()
  ├── def _write_rows()
  ├── def export_today()
  ├── def export_all()
  └── def export_by_date()

archive/legacy-ui/v1/python/__init__.py
  └── [no class/function definitions detected]

archive/legacy-ui/v1/python/config.py
  ├── def discover_serial_ports()
  └── def get_default_com_port()

archive/legacy-ui/v1/python/core/__init__.py
  └── [no class/function definitions detected]

archive/legacy-ui/v1/python/core/attendance.py
  ├── class AttendanceProcessor()
  ├── def __init__()
  ├── def process_line()
  └── def reset()

archive/legacy-ui/v1/python/core/commands.py
  ├── def cmd_scan()
  ├── def cmd_stop()
  ├── def build_enroll_command()
  ├── def cmd_enroll()
  ├── def cmd_delete()
  ├── def cmd_wipe()
  └── def cmd_list()

archive/legacy-ui/v1/python/core/database.py
  ├── def get_connection()
  ├── def init_database()
  ├── def add_student()
  ├── def update_student()
  ├── def delete_student()
  ├── def clear_all_students()
  ├── def get_student()
  ├── def get_all_students()
  ├── def get_student_count()
  ├── def register_student()
  ├── def import_students_from_list()
  ├── def log_attendance()
  ├── def get_attendance_today()
  ├── def get_attendance_all()
  ├── def get_attendance_paginated()
  ├── def get_attendance_count_today()
  ├── def get_attendance_by_date()
  ├── def clear_all_attendance()
  ├── def clear_all_data()
  ├── def get_attendance_by_student()
  ├── def get_students_by_grade_section()
  ├── def count_attendance_by_date()
  ├── def get_attendance_statistics()
  ├── def get_students_statistics()
  ├── def export_attendance_range()
  ├── def generate_statistics_report()
  ├── def generate_attendance_chart()
  ├── def generate_section_chart()
  ├── def generate_grade_chart()
  ├── def backup_database()
  ├── def restore_database()
  └── def list_backups()

archive/legacy-ui/v1/python/core/logger.py
  ├── class ColorFormatter()
  ├── def format()
  ├── class Logger()
  ├── def __init__()
  ├── def debug()
  ├── def info()
  ├── def success()
  ├── def warning()
  ├── def error()
  └── def critical()
```


### 2.3E Archive symbols — continued legacy UI

```text
archive/legacy-ui/v1/python/core/serial_handler.py
  ├── def list_serial_ports()
  ├── class SerialHandler()
  ├── def __init__()
  ├── def list_available_ports()
  ├── def connect()
  ├── def disconnect()
  ├── def send_command()
  ├── def read_line()
  ├── def should_ignore()
  ├── def is_connected()
  └── def auto_reconnect()

archive/legacy-ui/v1/python/core/utils.py
  ├── def get_export_path()
  ├── def timestamp_filename()
  ├── def format_datetime()
  ├── def today_str()
  ├── def now_str()
  └── def format_attendance_display()

archive/legacy-ui/v1/python/fix_emoji.py
  └── [no class/function definitions detected]

archive/legacy-ui/v1/python/gui/__init__.py
  └── [no class/function definitions detected]

archive/legacy-ui/v1/python/gui/app.py
  ├── def _logo_path()
  ├── class FingerprintApp()
  ├── def __init__()
  ├── def init_database()
  ├── def _apply_saved_settings()
  ├── def _apply_settings_to_runtime()
  ├── def save_current_settings()
  ├── def has_permission()
  ├── def update_button_permissions()
  ├── def change_role()
  ├── def _on_role_changed()
  ├── def build_ui()
  ├── def build_sidebar()
  ├── def switch_page()
  ├── def build_main_area()
  ├── def _on_attendance_mode_changed()
  ├── def _update_load_more_visibility()
  ├── def refresh_statistics()
  ├── def show_statistics_report()
  ├── def export_statistics_report()
  ├── def show_statistics_charts()
  ├── def toggle_connection()
  ├── def _set_connected_ui()
  ├── def refresh_serial_ports()
  ├── def open_settings_dialog()
  ├── def _set_disconnected_ui()
  ├── def _set_reconnect_ui()
  ├── def start_scan()
  ├── def stop_scan()
  ├── def start_reader_thread()
  ├── def read_serial_output()
  ├── def enroll_sample()
  ├── def list_fingerprints()
  ├── def open_enroll_dialog()
  ├── def save_enroll_profile()
  ├── def close_enroll_dialog()
  ├── def _parse_attendance()
  ├── def _parse_enroll_progress()
  ├── def open_wipe_dialog()
  ├── def confirm_wipe()
  ├── def close_wipe_dialog()
  ├── def _parse_wipe_progress()
  ├── def open_students_list_dialog()
  ├── def close_students_dialog()
  ├── def _clear_database_data()
  ├── def refresh_student_list()
  ├── def delete_student_from_list()
  ├── def open_edit_dialog()
  ├── def backup_database()
  ├── def open_restore_dialog()
  ├── def quit_app()
  ├── def _ui_ready()
  ├── def toggle_attendance_view()
  ├── def refresh_attendance_view()
  ├── def load_more_attendance()
  ├── def _build_attendance_card()
  ├── def open_add_student_dialog()
  ├── def log_message()
  ├── def _append_log_message()
  ├── def clear_log()
  └── def main()

archive/legacy-ui/v1/python/gui/attendance_page.py
  ├── class AttendancePage()
  ├── def __init__()
  ├── def build()
  ├── def refresh()
  ├── def load_more()
  ├── def build_card()
  ├── def _show_unknown_details()
  ├── def build_attendance_tab()
  ├── def refresh_attendance_view()
  ├── def load_more_attendance()
  └── def build_attendance_card()

archive/legacy-ui/v1/python/gui/dashboard.py
  ├── class DashboardPage()
  ├── def __init__()
  ├── def build()
  └── def refresh()

archive/legacy-ui/v1/python/gui/dialogs.py
  ├── def create_modal_dialog()
  ├── def ask_confirmation()
  ├── def open_enroll_dialog()
  ├── def save_enroll_profile()
  ├── def close_enroll_dialog()
  ├── def open_wipe_dialog()
  ├── def confirm_wipe()
  ├── def close_wipe_dialog()
  └── def open_restore_dialog()

archive/legacy-ui/v1/python/gui/log_page.py
  └── def build_log_tab()

archive/legacy-ui/v1/python/gui/main_window.py
  ├── class MainWindow()
  ├── def __init__()
  ├── def _build_ui()
  └── def run_gui()

archive/legacy-ui/v1/python/gui/reports_page.py
  ├── def show_statistics_report()
  ├── def export_statistics_report()
  ├── def show_statistics_charts()
  ├── def _display_chart_in_tab()
  └── def _copy_to_clipboard()

archive/legacy-ui/v1/python/gui/settings_dialog.py
  ├── def open_settings_dialog()
  ├── def _save_settings()
  └── def _refresh_ports()

archive/legacy-ui/v1/python/gui/settings_page.py
  ├── class SettingsPage()
  ├── def __init__()
  ├── def build()
  ├── def save()
  └── def refresh()
```


### 2.3F Archive symbols — legacy stack

```text
archive/legacy-ui/v1/python/gui/sidebar.py
  ├── def build_sidebar()
  └── def _add_action_button()

archive/legacy-ui/v1/python/gui/statistics_page.py
  └── def build_statistics_tab()

archive/legacy-ui/v1/python/gui/students_page.py
  ├── class StudentsPage()
  ├── def __init__()
  ├── def open_list_dialog()
  ├── def close_dialog()
  ├── def refresh()
  ├── def _build_student_row()
  ├── def delete_student()
  ├── def open_edit_dialog()
  ├── def do_save()
  ├── def do_delete()
  ├── def open_add_student_dialog()
  ├── def do_save()
  ├── def _get_page()
  ├── def open_students_list_dialog()
  ├── def close_students_dialog()
  ├── def refresh_student_list()
  ├── def delete_student_from_list()
  ├── def open_edit_dialog()
  └── def open_add_student_dialog()

archive/legacy-ui/v1/python/gui/theme.py
  ├── def apply_default_theme()
  ├── def apply_light_theme()
  └── def toggle_theme()

archive/legacy-ui/v1/python/gui/widgets.py
  ├── def section_header()
  ├── def card_frame()
  ├── def action_button()
  └── def subtle_label()

archive/legacy-ui/v1/python/main.py
  ├── def input_thread()
  └── def main()

archive/legacy-ui/v1/python/services/__init__.py
  └── [no class/function definitions detected]

archive/legacy-ui/v1/python/services/attendance_service.py
  ├── class AttendanceService()
  ├── def get_today()
  ├── def get_paginated()
  └── def log()

archive/legacy-ui/v1/python/services/backup.py
  └── def backup_database()

archive/legacy-ui/v1/python/services/excel_export.py
  ├── def _style_sheet()
  ├── def _write_rows()
  ├── def export_today()
  ├── def export_all()
  └── def export_by_date()

archive/legacy-ui/v1/python/services/student_service.py
  ├── class StudentService()
  ├── def get_all_students()
  ├── def get_student()
  ├── def save_student()
  └── def delete_student()

archive/legacy-ui/v1/python/settings_store.py
  ├── def default_settings()
  ├── def load_settings()
  └── def save_settings()

archive/legacy-ui/v2/python/__init__.py
  └── [no class/function definitions detected]
```


### 2.3G Archive symbols — legacy applications and helpers

```text
archive/legacy-ui/v2/python/config.py
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

archive/legacy-ui/v2/python/core/__init__.py
  └── [no class/function definitions detected]

archive/legacy-ui/v2/python/core/attendance.py
  ├── class ScanResult()
  ├── class ScanOutcome()
  ├── def to_dict()
  ├── class AttendanceProcessor()
  ├── def __init__()
  ├── def process_line()
  ├── def reset()
  ├── def lookup_student()
  ├── def all_students()
  ├── def _handle_unknown_scan()
  ├── def _handle_confidence_scan()
  ├── def _handle_json_match_scan()
  ├── def _parse_json_int()
  ├── def _parse_int_value()
  ├── def _is_in_cooldown()
  ├── def _cooldown_reason()
  └── def _log_and_record()

archive/legacy-ui/v2/python/core/commands.py
  ├── def cmd_scan()
  ├── def cmd_stop()
  ├── def build_enroll_command()
  ├── def cmd_enroll()
  ├── def cmd_delete()
  ├── def cmd_wipe()
  └── def cmd_list()

archive/legacy-ui/v2/python/core/database.py
  ├── class ValidationState()
  ├── class FieldValidationResult()
  ├── def _is_valid_name_character()
  ├── def _is_valid_student_name()
  ├── def _collect_unsupported_characters()
  ├── def _collect_unsupported_name_characters()
  ├── def _format_unsupported_characters()
  ├── class ManagedConnection()
  ├── def __init__()
  ├── def __enter__()
  ├── def __exit__()
  ├── def close()
  ├── def __getattr__()
  ├── class AttendanceRow()
  ├── class StudentRow()
  ├── def get_connection()
  ├── def _row_dicts()
  ├── def init_database()
  ├── def _migrate_attendance_event_type()
  ├── def validate_student_input()
  ├── def get_student_field_feedback()
  ├── def add_feedback()
  ├── def check_name()
  ├── def check_token()
  ├── def add_student()
  ├── def update_student()
  ├── def delete_student()
  ├── def clear_all_students()
  ├── def get_student()
  ├── def get_all_students()
  ├── def get_student_count()
  ├── def register_student()
  ├── def import_students_from_list()
  ├── def log_attendance()
  ├── def get_attendance_today()
  ├── def get_today_attendance_info()
  ├── def get_attendance_all()
  ├── def get_attendance_paginated()
  ├── def get_attendance_count_today()
  ├── def get_daily_attendance_summary()
  ├── def get_attendance_by_date()
  ├── def clear_all_attendance()
  ├── def clear_all_data()
  ├── def get_attendance_by_student()
  ├── def get_students_by_grade_section()
  ├── def count_attendance_by_date()
  ├── def get_attendance_statistics()
  ├── def get_students_statistics()
  ├── def export_attendance_range()
  ├── def generate_statistics_report()
  ├── def _save_chart()
  ├── def generate_attendance_chart()
  ├── def generate_section_chart()
  ├── def generate_grade_chart()
  ├── def backup_database()
  ├── def _is_path_within_directory()
  ├── def restore_database()
  ├── def list_backups()
  └── def auto_backup_if_needed()

archive/legacy-ui/v2/python/core/device_discovery.py
  ├── def list_serial_ports()
  ├── def _score_port_info()
  ├── def _ordered_candidate_ports()
  ├── def add_port()
  ├── def _parse_json_line()
  ├── def _validate_handshake()
  ├── def _probe_port()
  ├── def _accept_handshake()
  └── def discover_device()

archive/legacy-ui/v2/python/core/firmware_helper.py
  ├── def discover_firmware_candidates()
  ├── def find_firmware_binary()
  ├── def find_arduino_firmware()
  ├── def esptool_available()
  ├── def build_upload_command()
  ├── def upload_firmware()
  └── def upload_firmware_with_progress()

archive/legacy-ui/v2/python/core/logger.py
  ├── class AppFormatter()
  ├── def formatTime()
  ├── def format()
  ├── def _derive_source()
  ├── def _format_structured()
  ├── def _prune_old_logs()
  ├── def _configure_logger()
  ├── def _log_with_structured()
  ├── def debug()
  ├── def info()
  ├── def success()
  ├── def warning()
  ├── def error()
  ├── def critical()
  ├── def exception()
  ├── class LoggerProxy()
  ├── def debug()
  ├── def info()
  ├── def success()
  ├── def warning()
  ├── def error()
  ├── def critical()
  └── def exception()

archive/legacy-ui/v2/python/core/permissions.py
  ├── def get_current_role()
  ├── def has_permission()
  └── def require_permission()

archive/legacy-ui/v2/python/core/serial_handler.py
  ├── def list_serial_ports()
  ├── def build_common_port_candidates()
  ├── class SerialHandler()
  ├── def __init__()
  ├── def pyserial_installed()
  ├── def list_available_ports()
  ├── def connect()
  ├── def disconnect()
  ├── def test_connection()
  ├── def send_command()
  ├── def reset_device()
  ├── def read_line()
  ├── def should_ignore()
  ├── def is_connected()
  ├── def auto_reconnect()
  ├── def _schedule_reconnect()
  ├── def _join_reconnect_thread()
  ├── def _reconnect_worker()
  └── def _attempt_connect()

archive/legacy-ui/v2/python/core/utils.py
  ├── def parse_json_line()
  ├── def get_export_path()
  ├── def timestamp_filename()
  ├── def format_datetime()
  ├── def today_str()
  ├── def now_str()
  └── def format_attendance_display()

archive/legacy-ui/v2/python/customtkinter.py
  ├── class CTk()
  ├── class CTkFrame()
  ├── class CTkLabel()
  ├── class CTkButton()
  ├── def set_default_color_theme()
  ├── def set_appearance_mode()
  └── def get_appearance_mode()

archive/legacy-ui/v2/python/gui/__init__.py
  └── [no class/function definitions detected]
```


### 2.3H Archive symbols — legacy source continuation

```text
archive/legacy-ui/v2/python/gui/app.py
  ├── class FingerprintApp()
  ├── def __init__()
  ├── def init_database()
  ├── def _apply_saved_settings()
  ├── def _apply_settings_to_runtime()
  ├── def save_current_settings()
  ├── def _get_selected_port()
  ├── def _get_selected_baud_rate()
  ├── def _apply_connection_ui_state()
  ├── def _parse_attendance()
  ├── def has_permission()
  ├── def update_button_permissions()
  ├── def change_role()
  ├── def _on_role_changed()
  ├── def build_ui()
  ├── def build_sidebar()
  ├── def switch_page()
  ├── def build_main_area()
  ├── def _on_attendance_mode_changed()
  ├── def _update_load_more_visibility()
  ├── def refresh_statistics()
  ├── def show_statistics_report()
  ├── def export_statistics_report()
  ├── def show_statistics_charts()
  ├── def toggle_connection()
  ├── def _set_connected_ui()
  ├── def _on_serial_connected()
  ├── def _on_serial_connection_failed()
  ├── def refresh_serial_ports()
  ├── def open_settings_dialog()
  ├── def show_serial_help()
  ├── def auto_detect_serial_on_startup()
  ├── def try_common_serial_ports()
  ├── def _set_disconnected_ui()
  ├── def _set_reconnect_ui()
  ├── def _set_scan_mode_ui()
  ├── def _set_command_mode_ui()
  ├── def _set_enroll_mode_ui()
  ├── def _set_wipe_mode_ui()
  ├── def _clear_enroll_mode_ui()
  ├── def _parse_connection_mode()
  ├── def _schedule_attendance_refresh()
  ├── def _refresh_attendance_view_safe()
  ├── def start_scan()
  ├── def stop_scan()
  ├── def start_reader_thread()
  ├── def stop_reader_thread()
  ├── def read_serial_output()
  ├── def enroll_sample()
  ├── def list_fingerprints()
  ├── def open_enroll_dialog()
  ├── def save_enroll_profile()
  ├── def close_enroll_dialog()
  ├── def _dispatch_attendance_message()
  ├── def _handle_scan_result()
  ├── def _render_attendance_record()
  ├── def _parse_enroll_progress()
  ├── def open_wipe_dialog()
  ├── def confirm_wipe()
  ├── def close_wipe_dialog()
  ├── def _parse_wipe_progress()
  ├── def open_students_list_dialog()
  ├── def close_students_dialog()
  ├── def _clear_database_data()
  ├── def refresh_student_list()
  ├── def delete_student_from_list()
  ├── def open_edit_dialog()
  ├── def backup_database()
  ├── def open_restore_dialog()
  ├── def quit_app()
  ├── def _ui_ready()
  ├── def toggle_attendance_view()
  ├── def refresh_attendance_view()
  ├── def load_more_attendance()
  ├── def open_add_student_dialog()
  ├── def log_message()
  ├── def _append_log_message()
  ├── def clear_log()
  └── def main()

archive/legacy-ui/v2/python/gui/attendance_page.py
  ├── class AttendancePage()
  ├── def __init__()
  ├── def build()
  ├── def refresh()
  ├── def load_more()
  ├── def build_card()
  ├── def _show_unknown_details()
  ├── def build_attendance_tab()
  ├── def refresh_attendance_view()
  ├── def load_more_attendance()
  └── def build_attendance_card()

archive/legacy-ui/v2/python/gui/dashboard.py
  ├── class DashboardPage()
  ├── def __init__()
  ├── def build()
  └── def refresh()

archive/legacy-ui/v2/python/gui/dialogs.py
  ├── def create_modal_dialog()
  ├── def ask_confirmation()
  ├── def open_enroll_dialog()
  ├── def save_enroll_profile()
  ├── def close_enroll_dialog()
  ├── def open_wipe_dialog()
  ├── def confirm_wipe()
  ├── def close_wipe_dialog()
  └── def open_restore_dialog()

archive/legacy-ui/v2/python/gui/layout_utils.py
  ├── def scale_value()
  ├── def resolve_window_size()
  ├── def resolve_dialog_size()
  ├── def resolve_sidebar_width()
  └── def get_scaling_factor()

archive/legacy-ui/v2/python/gui/legacy/bfeas_app2.py
  └── [no class/function definitions detected]

archive/legacy-ui/v2/python/gui/legacy/reports_table_page.py
  ├── def _is_safe_path()
  ├── class ReportsPage()
  ├── def __init__()
  ├── class ReportsPage()
  └── def __init__()

archive/legacy-ui/v2/python/gui/log_page.py
  └── def build_log_tab()

archive/legacy-ui/v2/python/gui/perf_profiler.py
  ├── class PerfProfiler()
  ├── def __init__()
  ├── def start()
  ├── def stop()
  ├── def report()
  ├── def wrap()
  ├── class _Ctx()
  ├── def __enter__()
  └── def __exit__()

archive/legacy-ui/v2/python/gui/reports_page.py
  ├── def show_statistics_report()
  ├── def export_statistics_report()
  ├── def show_statistics_charts()
  ├── def _display_chart_in_tab()
  └── def _copy_to_clipboard()

archive/legacy-ui/v2/python/gui/serial_troubleshooting.py
  ├── def build_serial_troubleshooting_message()
  ├── def build_common_port_candidates()
  ├── def open_device_manager()
  └── def open_driver_help()

archive/legacy-ui/v2/python/gui/settings_dialog.py
  ├── def open_settings_dialog()
  ├── def _refresh_firmware_status()
  ├── def _upload_firmware()
  ├── def _progress()
  ├── def _run_upload()
  ├── def _save_settings()
  └── def _refresh_ports()

archive/legacy-ui/v2/python/gui/settings_page.py
  ├── class SettingsPage()
  ├── def __init__()
  ├── def build()
  ├── def save()
  └── def refresh()
```


### 2.3I Archive symbols — legacy source continuation

```text
archive/legacy-ui/v2/python/gui/sidebar.py
  ├── def build_sidebar()
  └── def _add_action_button()

archive/legacy-ui/v2/python/gui/statistics_page.py
  └── def build_statistics_tab()

archive/legacy-ui/v2/python/gui/students_page.py
  ├── class StudentsPage()
  ├── def __init__()
  ├── def open_list_dialog()
  ├── def close_dialog()
  ├── def refresh()
  ├── def _build_student_row()
  ├── def delete_student()
  ├── def open_edit_dialog()
  ├── def do_save()
  ├── def do_delete()
  ├── def open_add_student_dialog()
  ├── def do_save()
  ├── def _get_page()
  ├── def open_students_list_dialog()
  ├── def close_students_dialog()
  ├── def refresh_student_list()
  ├── def delete_student_from_list()
  ├── def open_edit_dialog()
  └── def open_add_student_dialog()

archive/legacy-ui/v2/python/gui/theme.py
  ├── def _normalize_mode()
  ├── def _apply_widget_theme()
  ├── def refresh_widget_theme_tree()
  ├── def apply_appearance_mode()
  ├── def _apply_once()
  ├── def get_theme_colors()
  ├── def apply_default_theme()
  ├── def apply_light_theme()
  └── def toggle_theme()

archive/legacy-ui/v2/python/gui_qt/__init__.py
  └── [no class/function definitions detected]

archive/legacy-ui/v2/python/gui_qt/main_qt.py
  ├── def _handle_uncaught_exception()
  ├── def _handle_thread_exception()
  ├── def _on_app_about_to_quit()
  ├── def _on_process_exit()
  ├── def apply_base_style()
  ├── def _build_palette()
  ├── def apply_theme()
  ├── def load_stylesheet()
  └── def main()

archive/legacy-ui/v2/python/gui_qt/main_window.py
  ├── def _logo_path()
  ├── class MainWindow()
  ├── def __init__()
  ├── def _configure_auto_backup_timer()
  ├── def _run_auto_backup_check()
  ├── def switch_page()
  ├── def _apply_role_permissions()
  ├── def _set_connect_button_state()
  ├── def on_connect_clicked()
  ├── def on_connect_result()
  ├── def on_connection_settings_changed()
  ├── class _LogBridge()
  ├── class _QtLogHandler()
  ├── def __init__()
  ├── def emit()
  ├── def _create_log_handler()
  ├── def on_connection_changed()
  ├── def on_scan_event()
  ├── def on_serial_error()
  ├── def on_scan_mode_changed()
  ├── def _update_scan_toggle_button()
  ├── def _set_scan_block_reason()
  ├── def _clear_scan_block_reason()
  ├── def _scan_command_blocked_reason()
  ├── def _can_start_scan()
  ├── def on_scan_toggle_clicked()
  ├── def update_connection_metadata()
  └── def closeEvent()

archive/legacy-ui/v2/python/gui_qt/pages/__init__.py
  └── [no class/function definitions detected]

archive/legacy-ui/v2/python/gui_qt/pages/attendance_page.py
  ├── class AttendancePage()
  ├── def __init__()
  ├── def _on_mode_changed()
  ├── def _is_recent_mode()
  ├── def _is_last_30_days_mode()
  ├── def refresh()
  ├── def _update_pagination_controls()
  ├── def on_prev_clicked()
  ├── def on_next_clicked()
  ├── def _populate()
  └── def on_scan_event()

archive/legacy-ui/v2/python/gui_qt/pages/dashboard_page.py
  ├── class DashboardPage()
  ├── def __init__()
  ├── def _format_item_text()
  ├── def refresh()
  ├── def refresh_dashboard()
  └── def on_scan_event()

archive/legacy-ui/v2/python/gui_qt/pages/logs_page.py
  ├── class LogsPage()
  ├── def __init__()
  ├── def console()
  ├── def monitor()
  ├── def clear()
  ├── def append_line()
  ├── def append_serial_line()
  ├── def append_record()
  ├── def set_connection_state()
  ├── def set_connection_info()
  ├── def clear_app_log()
  ├── def clear_monitor()
  ├── def pause_monitor()
  ├── def resume_monitor()
  ├── def _set_auto_scroll()
  ├── def send_command()
  ├── def send_list_command()
  ├── def reset_device()
  ├── def _append_app_text()
  └── def _append_serial_text()

archive/legacy-ui/v2/python/gui_qt/pages/reports_page.py
  ├── def _sanitize_csv_cell()
  ├── class ReportsPage()
  ├── def __init__()
  ├── def refresh_backup_list()
  ├── def refresh()
  ├── def refresh_report()
  ├── def on_export_clicked()
  ├── def on_backup_clicked()
  └── def on_restore_clicked()

archive/legacy-ui/v2/python/gui_qt/pages/settings_page.py
  ├── class SettingsPage()
  ├── def __init__()
  ├── def _section_label()
  ├── def refresh()
  ├── def refresh_connection_status()
  ├── def _update_permissions_label()
  ├── def _open_folder()
  ├── def _apply_theme()
  ├── def _populate_ports()
  ├── def _forget_saved_port()
  └── def on_save()
```

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

