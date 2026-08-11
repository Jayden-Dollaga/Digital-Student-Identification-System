# Code Metrics Audit

## Summary

- Included source files: 161
- Active source files: 107
- Legacy/duplicate/generated source files: 54
- Total physical lines (included source files): 22404
- Total code lines (included source files): 13041
- Total comment lines: 5811
- Total blank lines: 3552

## Language Breakdown

| Language | Files | Total Lines | Blank | Comments | Code |
|---|---:|---:|---:|---:|---:|
| Python | 146 | 20390 | 3310 | 5577 | 11503 |
| Arduino/C++ | 8 | 1876 | 225 | 228 | 1423 |
| C | 0 | 0 | 0 | 0 | 0 |
| JavaScript | 0 | 0 | 0 | 0 | 0 |
| Shell | 7 | 138 | 17 | 6 | 115 |
| Other | 0 | 0 | 0 | 0 | 0 |

## Component Breakdown

| Component | Files | Physical LOC | Code LOC |
|---|---:|---:|---:|
| ESP32 Firmware | 5 | 1492 | 1125 |
| Python Backend | 21 | 3278 | 1560 |
| Qt GUI | 45 | 3779 | 1887 |
| Legacy GUI | 33 | 7100 | 4327 |
| Tests | 40 | 5084 | 2850 |
| Tools/Scripts | 16 | 1332 | 975 |
| Other | 1 | 339 | 317 |

## Largest Files by Physical Lines

| Path | Language | Physical | Blank | Comments | Code |
|---|---|---:|---:|---:|---:|
| archive/legacy-ui/testing_area/gui/legacy/app_test1.py | Python | 1826 | 234 | 543 | 1049 |
| tests/app_test.py | Python | 1209 | 154 | 394 | 661 |
| python/gui/app.py | Python | 1120 | 156 | 228 | 736 |
| python/core/database.py | Python | 831 | 145 | 133 | 553 |
| firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino | Arduino/C++ | 803 | 92 | 90 | 621 |
| tools/_database_refactor.py | Python | 733 | 135 | 104 | 494 |
| python/core/serial_handler.py | Python | 580 | 56 | 290 | 234 |
| tests/whs_dashboard.py | Python | 532 | 90 | 64 | 378 |
| archive/legacy-ui/testing_area/gui/legacy/bfeas_app2.py | Python | 499 | 85 | 380 | 34 |
| python/gui/students_page.py | Python | 443 | 64 | 5 | 374 |
| archive/legacy-ui/testing_area/gui/legacy/reports_table_page.py | Python | 396 | 70 | 37 | 289 |
| python/gui_qt/pages/students_page.py | Python | 381 | 50 | 216 | 115 |
| python/gui_qt/main_window.py | Python | 372 | 48 | 31 | 293 |
| tests/legacy/phase2_databasev3.py | Python | 346 | 52 | 101 | 193 |
| audit/generate_metrics.py | Python | 339 | 22 | 0 | 317 |
| python/core/device_discovery.py | Python | 329 | 51 | 141 | 137 |
| tests/legacy/phase2_databasev4.py | Python | 320 | 48 | 102 | 170 |
| archive/legacy-ui/gui_qt_redesign_2/gui_qt/pages/students_page.py | Python | 301 | 40 | 169 | 92 |
| tests/test_gui_demo.py | Python | 293 | 48 | 212 | 33 |
| python/gui_qt/pages/settings_page.py | Python | 289 | 52 | 95 | 142 |

## Largest Files by Code Lines

| Path | Language | Physical | Blank | Comments | Code |
|---|---|---:|---:|---:|---:|
| archive/legacy-ui/testing_area/gui/legacy/app_test1.py | Python | 1826 | 234 | 543 | 1049 |
| python/gui/app.py | Python | 1120 | 156 | 228 | 736 |
| tests/app_test.py | Python | 1209 | 154 | 394 | 661 |
| firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino | Arduino/C++ | 803 | 92 | 90 | 621 |
| python/core/database.py | Python | 831 | 145 | 133 | 553 |
| tools/_database_refactor.py | Python | 733 | 135 | 104 | 494 |
| tests/whs_dashboard.py | Python | 532 | 90 | 64 | 378 |
| python/gui/students_page.py | Python | 443 | 64 | 5 | 374 |
| audit/generate_metrics.py | Python | 339 | 22 | 0 | 317 |
| python/gui_qt/main_window.py | Python | 372 | 48 | 31 | 293 |
| archive/legacy-ui/testing_area/gui/legacy/reports_table_page.py | Python | 396 | 70 | 37 | 289 |
| archive/diagnostics/serial_monitor_test.py | Python | 286 | 31 | 1 | 254 |
| python/core/serial_handler.py | Python | 580 | 56 | 290 | 234 |
| python/gui/dialogs.py | Python | 271 | 53 | 1 | 217 |
| firmware/test/fingerprint_check/fingerprint_check.ino | Arduino/C++ | 263 | 32 | 26 | 205 |
| python/gui/attendance_page.py | Python | 241 | 39 | 0 | 202 |
| archive/legacy-ui/testing_area/gui/legacy/bfeas_app.py | Python | 256 | 45 | 17 | 194 |
| tests/legacy/phase2_databasev3.py | Python | 346 | 52 | 101 | 193 |
| firmware/enroll/enroll.ino | Arduino/C++ | 213 | 23 | 16 | 174 |
| python/core/attendance.py | Python | 271 | 40 | 58 | 173 |

## Excluded / Special Cases

- Excluded directories: .git, .hg, .mypy_cache, .pytest_cache, .svn, .venv, .venv-1, .vscode, __pycache__, build, dist, env, node_modules, site-packages, venv
- Archive, legacy, experimental, duplicate, backup, and generated files were included in the inventory and reported separately as non-active source.

## Git History

- Commits: 38
- First commit date: 2026-08-09T19:20:05+08:00
- Latest commit date: 2026-08-09T19:20:05+08:00
- Files changed in history (unique): 38
- Historical lines added: 45761
- Historical lines deleted: 6450
- Historical net change: 39311

## Methodology

- Source files were discovered by extension across the repository tree.
- Excluded directories were skipped, including .git, virtual environments, caches, build artifacts, and dependency folders.
- Physical lines are counted directly from file contents. Blank lines are whitespace-only. Comment-only lines are detected with language-aware heuristics; code lines are the remainder.
- Legacy/duplicate/generated files are called out separately so the headline totals can distinguish active source from archived or copy-like files.