# Code Metrics Audit

## Summary

- Included source files: 181
- Active source files: 127
- Legacy/duplicate/generated source files: 54
- Total physical lines (included source files): 27524
- Total code lines (included source files): 14117
- Total comment lines: 8952
- Total blank lines: 4455

## Language Breakdown

| Language | Files | Total Lines | Blank | Comments | Code |
|---|---:|---:|---:|---:|---:|
| Python | 165 | 25482 | 4209 | 8711 | 12562 |
| Arduino/C++ | 8 | 1882 | 226 | 233 | 1423 |
| C | 0 | 0 | 0 | 0 | 0 |
| JavaScript | 0 | 0 | 0 | 0 | 0 |
| Shell | 8 | 160 | 20 | 8 | 132 |
| Other | 0 | 0 | 0 | 0 | 0 |

## Component Breakdown

| Component | Files | Physical LOC | Code LOC |
|---|---:|---:|---:|
| ESP32 Firmware | 5 | 1498 | 1125 |
| Python Backend | 22 | 4006 | 1690 |
| Qt GUI | 46 | 5097 | 2176 |
| Legacy GUI | 33 | 7194 | 4374 |
| Tests | 56 | 7823 | 3299 |
| Tools/Scripts | 17 | 1544 | 1119 |
| Other | 2 | 362 | 334 |

## Largest Files by Physical Lines

| Path | Language | Physical | Blank | Comments | Code |
|---|---|---:|---:|---:|---:|
| archive/legacy-ui/testing_area/gui/legacy/app_test1.py | Python | 1826 | 234 | 543 | 1049 |
| python/core/database.py | Python | 1235 | 218 | 394 | 623 |
| tests/app_test.py | Python | 1209 | 154 | 394 | 661 |
| python/gui/app.py | Python | 1129 | 156 | 236 | 737 |
| firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino | Arduino/C++ | 803 | 92 | 90 | 621 |
| tools/_database_refactor.py | Python | 733 | 135 | 104 | 494 |
| python/gui_qt/pages/students_page.py | Python | 696 | 97 | 454 | 145 |
| python/core/serial_handler.py | Python | 678 | 62 | 377 | 239 |
| python/gui_qt/pages/settings_page.py | Python | 582 | 92 | 301 | 189 |
| python/gui_qt/main_window.py | Python | 578 | 75 | 169 | 334 |
| tests/whs_dashboard.py | Python | 532 | 90 | 64 | 378 |
| archive/legacy-ui/testing_area/gui/legacy/bfeas_app2.py | Python | 499 | 85 | 380 | 34 |
| python/gui/students_page.py | Python | 451 | 64 | 5 | 382 |
| tests/test_enrollment_dialog_ux.py | Python | 446 | 105 | 325 | 16 |
| python/core/device_discovery.py | Python | 429 | 59 | 180 | 190 |
| archive/legacy-ui/testing_area/gui/legacy/reports_table_page.py | Python | 396 | 70 | 37 | 289 |
| tests/legacy/phase2_databasev3.py | Python | 346 | 52 | 101 | 193 |
| audit/generate_metrics.py | Python | 341 | 23 | 1 | 317 |
| tests/legacy/phase2_databasev4.py | Python | 320 | 48 | 102 | 170 |
| archive/legacy-ui/gui_qt_redesign_2/gui_qt/pages/students_page.py | Python | 301 | 40 | 169 | 92 |

## Largest Files by Code Lines

| Path | Language | Physical | Blank | Comments | Code |
|---|---|---:|---:|---:|---:|
| archive/legacy-ui/testing_area/gui/legacy/app_test1.py | Python | 1826 | 234 | 543 | 1049 |
| python/gui/app.py | Python | 1129 | 156 | 236 | 737 |
| tests/app_test.py | Python | 1209 | 154 | 394 | 661 |
| python/core/database.py | Python | 1235 | 218 | 394 | 623 |
| firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino | Arduino/C++ | 803 | 92 | 90 | 621 |
| tools/_database_refactor.py | Python | 733 | 135 | 104 | 494 |
| python/gui/students_page.py | Python | 451 | 64 | 5 | 382 |
| tests/whs_dashboard.py | Python | 532 | 90 | 64 | 378 |
| python/gui_qt/main_window.py | Python | 578 | 75 | 169 | 334 |
| audit/generate_metrics.py | Python | 341 | 23 | 1 | 317 |
| archive/legacy-ui/testing_area/gui/legacy/reports_table_page.py | Python | 396 | 70 | 37 | 289 |
| archive/diagnostics/serial_monitor_test.py | Python | 286 | 31 | 1 | 254 |
| python/core/serial_handler.py | Python | 678 | 62 | 377 | 239 |
| python/gui/dialogs.py | Python | 274 | 53 | 1 | 220 |
| firmware/test/fingerprint_check/fingerprint_check.ino | Arduino/C++ | 263 | 32 | 26 | 205 |
| python/gui/attendance_page.py | Python | 243 | 40 | 1 | 202 |
| archive/legacy-ui/testing_area/gui/legacy/bfeas_app.py | Python | 256 | 45 | 17 | 194 |
| tests/legacy/phase2_databasev3.py | Python | 346 | 52 | 101 | 193 |
| python/core/device_discovery.py | Python | 429 | 59 | 180 | 190 |
| python/gui_qt/pages/settings_page.py | Python | 582 | 92 | 301 | 189 |

## Excluded / Special Cases

- Excluded directories: .git, .hg, .mypy_cache, .pytest_cache, .svn, .venv, .venv-1, .vscode, __pycache__, build, dist, env, node_modules, site-packages, venv
- Archive, legacy, experimental, duplicate, backup, and generated files were included in the inventory and reported separately as non-active source.

## Git History

- Commits: 63
- First commit date: 2026-08-28T00:51:19+08:00
- Latest commit date: 2026-08-28T00:51:19+08:00
- Files changed in history (unique): 63
- Historical lines added: 62411
- Historical lines deleted: 8557
- Historical net change: 53854

## Methodology

- Source files were discovered by extension across the repository tree.
- Excluded directories were skipped, including .git, virtual environments, caches, build artifacts, and dependency folders.
- Physical lines are counted directly from file contents. Blank lines are whitespace-only. Comment-only lines are detected with language-aware heuristics; code lines are the remainder.
- Legacy/duplicate/generated files are called out separately so the headline totals can distinguish active source from archived or copy-like files.