# Digital Student Identification System

DSIS is a Windows desktop attendance system for schools and training centers. An ESP32 and AS608 fingerprint sensor handle enrollment and identification; the Python application manages student records, attendance history, reports, backups, and serial communication.

## Features

- Fingerprint enrollment, matching, deletion, and device wipe
- SQLite student and attendance records
- Qt dashboard, attendance, students, reports, logs, and settings pages
- Attendance cooldown handling and confidence-aware scan processing
- CSV/report exports and database backups with role-based UI permissions
- ESP32 device discovery, connection status, firmware assistance, and serial diagnostics

## Screenshots

![DSIS Main](docs/UserGuide/images/Screenshot_2026-08-28_014145.png)

![Fingerprint Report Page](docs/UserGuide/images/Screenshot_2026-08-28_014206.png)

## Quick Start

1. Install Python and project dependencies:

   ```text
   python -m pip install -r requirements.txt
   ```

2. Upload the all-in-one firmware once using Arduino IDE. See [Installation](INSTALLATION.md) for wiring, board, and firmware details.

3. Connect the ESP32, close other serial monitors, and launch the active Qt application:

   ```text
   run_qt_gui.bat
   ```

For packaged Windows deployment, see [Portable Build](PORTABLE_BUILD.md). For connection problems, see [Troubleshooting](docs/TROUBLESHOOTING.md).

## Active Interfaces

The maintained desktop interface is the PySide6/Qt application launched by [run_qt_gui.py](run_qt_gui.py) or [run_qt_gui.bat](run_qt_gui.bat). The older CustomTkinter interface remains available through [run_app.bat](run_app.bat) for compatibility and is not the primary workflow.

## Project Structure

| Path | Purpose |
| --- | --- |
| `python/` | Python application, services, serial handling, database, and UI code |
| `firmware/` | ESP32 and AS608 Arduino sketches |
| `data/` | Runtime settings, database, backups, logs, and charts |
| `tests/` | Automated regression and integration tests |
| `tools/` | Diagnostics, packaging helpers, and maintenance scripts |
| `docs/` | User, architecture, hardware, development, security, and generated documentation |
| `archive/` | Historical and experimental material retained for reference |

See the [documentation index](docs/INDEX.md) for the full map.

## License

See [LICENSE](LICENSE).

Last verified: 2026-08-28, against commit 3119175
