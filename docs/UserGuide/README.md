# User Guide

The maintained DSIS desktop application is v3, launched with `run_web_gui.bat` or `python run_web_gui.py` on Windows.

## Guides

- [Installation Guide](installation-guide.md): Python setup, USB drivers, firmware, and launch.
- [v3 Workflows](v3-workflows.md): first-run setup, enrollment, attendance, students, reports, settings, and recovery.
- [Project Overview](project-overview.md): product scope and supported components.
- [Testing Results](testing-results.md): validation evidence for the recorded snapshot.

## Operational model

The web UI is local to the desktop process. pywebview renders HTML/CSS/JavaScript and provides a Python object through `window.pywebview.api`. The frontend requests data and actions through that bridge; Python reads SQLite and communicates with the ESP32 over USB serial. No hosted web service or network account is required for normal operation.

## Roles and first run

A fresh settings file has no usable administrator password. The first-run wizard requires an administrator password of at least eight characters, then may collect device, schedule, and branding settings. Passwords are stored as salted PBKDF2-HMAC-SHA256 records, not plaintext. Normal launches begin in the configured guest role; administrator elevation requires password authentication and is held in memory for the session timeout.

## Important behavior

- Enrolling a fingerprint on the sensor and saving the student record are coordinated but distinct operations. A failed save must be resolved before treating the student as enrolled.
- A matched scan is evaluated by the Python attendance processor. The configured minimum confidence determines `GOOD MATCH` versus `WEAK MATCH`; the configured per-fingerprint cooldown prevents rapid duplicate records.
- Unknown scans use reserved fingerprint ID `0` and the `Unregistered` placeholder row so they can be retained without pretending to identify a student.
- Database restore, wipe, student deletion, settings changes, backups, and exports are permission-gated operations.
