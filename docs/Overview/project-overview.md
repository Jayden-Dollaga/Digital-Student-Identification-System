# Project Overview

DSIS is a local-first fingerprint attendance system built for school or training-center operation. The maintained application is a Windows-native desktop app using `pywebview` to host a browser-style frontend, while the backend logic lives in Python and the persistent state lives in SQLite.

## What the app does

The application allows a user to:

- enroll students and assign fingerprint IDs,
- link and erase RC522 RFID card data,
- connect to an ESP32 device over USB serial,
- perform scans with the AS608 sensor,
- record attendance events,
- evaluate attendance over daily, weekly, and monthly windows,
- create and restore backups,
- export attendance and report data to CSV,
- manage schedule exceptions and permissions.

## Active runtime architecture

```text
Browser UI / pywebview
    -> python/gui_web/api.py
        -> core.database / core.serial_handler / core.attendance
            -> SQLite database (data/attendance.db)
            -> ESP32 + AS608 + RC522 over USB/serial
```

The UI is not a separate service. It is a local page rendered by the app and connected directly to Python via the `window.pywebview.api` bridge.

## Responsibility boundaries

- `python/gui_web/` — front-end shell and bridge
- `python/core/` — device, identity, attendance, permissions, and DB logic
- `python/services/` — workflow-oriented service layer helpers
- `firmware/` — active ESP32 + AS608 + RC522 firmware and archived variants
- `data/` — runtime settings, logs, exports, backups, SQLite DB

## Support model

The supported path for daily use is the v3 app. Older implementations remain in `archive/legacy-ui` and are historical references. They are not the primary operating interface for the active product.

## Security posture

DSIS is local-first and stores the primary operational data on disk in the local machine's `data/` directory. Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes and role-based permission checks are enforced in-memory through the session layer.

## What is not in scope

This repository is not a cloud SaaS product. There is no hosted backend or remote API server in the maintained runtime.
