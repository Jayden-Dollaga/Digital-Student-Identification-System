# Code Metrics Audit

## Summary

- Included source files: 305
- Active source files: 132
- Legacy/duplicate/generated source files: 173
- Total physical lines (included source files): 51143
- Total code lines (included source files): 24050
- Total comment lines: 19132
- Total blank lines: 7961

## Language Breakdown

| Language | Files | Total Lines | Blank | Comments | Code |
|---|---:|---:|---:|---:|---:|
| Python | 286 | 47800 | 7605 | 18850 | 21345 |
| Arduino/C++ | 8 | 1886 | 226 | 236 | 1424 |
| C | 0 | 0 | 0 | 0 | 0 |
| JavaScript | 1 | 1259 | 106 | 37 | 1116 |
| Shell | 10 | 198 | 24 | 9 | 165 |
| Other | 0 | 0 | 0 | 0 | 0 |

## Component Breakdown

| Component | Files | Physical LOC | Code LOC |
|---|---:|---:|---:|
| ESP32 Firmware | 5 | 1502 | 1126 |
| Python Backend | 21 | 5978 | 2659 |
| Qt GUI | 79 | 12595 | 4511 |
| Legacy GUI | 98 | 18992 | 9917 |
| Tests | 81 | 10132 | 4356 |
| Tools/Scripts | 17 | 1559 | 1132 |
| Other | 4 | 385 | 349 |

## Largest Files by Physical Lines

| Path | Language | Physical | Blank | Comments | Code |
|---|---|---:|---:|---:|---:|
| archive/legacy-ui/testing_area/gui/legacy/app_test1.py | Python | 1826 | 234 | 543 | 1049 |
| archive/legacy-ui/v1/python/core/database.py | Python | 1335 | 232 | 493 | 610 |
| archive/legacy-ui/v2/python/core/database.py | Python | 1335 | 232 | 493 | 610 |
| python/core/database.py | Python | 1335 | 232 | 493 | 610 |
| python/gui_web/web/app.js | JavaScript | 1259 | 106 | 37 | 1116 |
| tests/app_test.py | Python | 1209 | 154 | 394 | 661 |
| archive/legacy-ui/v1/python/gui/app.py | Python | 1129 | 156 | 236 | 737 |
| archive/legacy-ui/v2/python/gui/app.py | Python | 1125 | 155 | 236 | 734 |
| archive/legacy-ui/v1/python/gui_qt/pages/students_page.py | Python | 895 | 122 | 631 | 142 |
| archive/legacy-ui/v2/python/gui_qt/pages/students_page.py | Python | 895 | 122 | 631 | 142 |
| python/gui_web/v2_reference/gui_qt/pages/students_page.py | Python | 895 | 122 | 631 | 142 |
| python/gui_web/api.py | Python | 822 | 86 | 693 | 43 |
| firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino | Arduino/C++ | 807 | 92 | 93 | 622 |
| archive/legacy-ui/v1/python/core/serial_handler.py | Python | 752 | 65 | 448 | 239 |
| archive/legacy-ui/v2/python/core/serial_handler.py | Python | 752 | 65 | 448 | 239 |
| python/core/serial_handler.py | Python | 752 | 65 | 448 | 239 |
| tools/_database_refactor.py | Python | 733 | 135 | 104 | 494 |
| archive/legacy-ui/v1/python/gui_qt/main_window.py | Python | 628 | 83 | 211 | 334 |
| archive/legacy-ui/v2/python/gui_qt/main_window.py | Python | 628 | 83 | 211 | 334 |
| python/gui_web/v2_reference/gui_qt/main_window.py | Python | 628 | 83 | 211 | 334 |

## Largest Files by Code Lines

| Path | Language | Physical | Blank | Comments | Code |
|---|---|---:|---:|---:|---:|
| python/gui_web/web/app.js | JavaScript | 1259 | 106 | 37 | 1116 |
| archive/legacy-ui/testing_area/gui/legacy/app_test1.py | Python | 1826 | 234 | 543 | 1049 |
| archive/legacy-ui/v1/python/gui/app.py | Python | 1129 | 156 | 236 | 737 |
| archive/legacy-ui/v2/python/gui/app.py | Python | 1125 | 155 | 236 | 734 |
| tests/app_test.py | Python | 1209 | 154 | 394 | 661 |
| firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino | Arduino/C++ | 807 | 92 | 93 | 622 |
| archive/legacy-ui/v1/python/core/database.py | Python | 1335 | 232 | 493 | 610 |
| archive/legacy-ui/v2/python/core/database.py | Python | 1335 | 232 | 493 | 610 |
| python/core/database.py | Python | 1335 | 232 | 493 | 610 |
| tools/_database_refactor.py | Python | 733 | 135 | 104 | 494 |
| archive/legacy-ui/v1/python/gui/students_page.py | Python | 451 | 64 | 5 | 382 |
| archive/legacy-ui/v2/python/gui/students_page.py | Python | 451 | 64 | 5 | 382 |
| tests/whs_dashboard.py | Python | 532 | 90 | 64 | 378 |
| tests/Prototype/Python/prototype_window.py | Python | 447 | 42 | 54 | 351 |
| archive/legacy-ui/v1/python/gui_qt/main_window.py | Python | 628 | 83 | 211 | 334 |
| archive/legacy-ui/v2/python/gui_qt/main_window.py | Python | 628 | 83 | 211 | 334 |
| python/gui_web/v2_reference/gui_qt/main_window.py | Python | 628 | 83 | 211 | 334 |
| audit/generate_metrics.py | Python | 341 | 23 | 1 | 317 |
| archive/legacy-ui/testing_area/gui/legacy/reports_table_page.py | Python | 396 | 70 | 37 | 289 |
| archive/diagnostics/serial_monitor_test.py | Python | 286 | 31 | 1 | 254 |

## Excluded / Special Cases

- Excluded directories: .git, .hg, .mypy_cache, .pytest_cache, .svn, .venv, .venv-1, .vscode, __pycache__, build, dist, env, node_modules, site-packages, venv
- Archive, legacy, experimental, duplicate, backup, and generated files were included in the inventory and reported separately as non-active source.

## Git History

- Commits: 90
- First commit date: 2026-09-09T01:28:36+08:00
- Latest commit date: 2026-09-09T01:28:36+08:00
- Files changed in history (unique): 90
- Historical lines added: 107108
- Historical lines deleted: 23175
- Historical net change: 83933

## Methodology

- Source files were discovered by extension across the repository tree.
- Excluded directories were skipped, including .git, virtual environments, caches, build artifacts, and dependency folders.
- Physical lines are counted directly from file contents. Blank lines are whitespace-only. Comment-only lines are detected with language-aware heuristics; code lines are the remainder.
- Legacy/duplicate/generated files are called out separately so the headline totals can distinguish active source from archived or copy-like files.