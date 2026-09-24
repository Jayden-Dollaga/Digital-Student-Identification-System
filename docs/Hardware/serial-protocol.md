# ESP32 Serial Protocol

This is the current protocol implemented by the all-in-one ESP32 sketch and consumed by the Python serial layer.

## Links and baud rates

| Link | Baud | Owner |
| --- | ---: | --- |
| DSIS desktop to ESP32 USB serial | 115200 | `serial_handler.py` and firmware `Serial` |
| ESP32 to AS608 UART | 57600 | firmware `HardwareSerial(2)` and `Adafruit_Fingerprint` |

The desktop must not use the sensor baud rate directly.

## Host commands

The active firmware accepts `ID?`, `SCAN`, `STOP`, `ENROLL`, `ENROLL:<id>`, `DELETE:<id>`, `WIPE`, and `LIST`. The RFID-capable sketch also handles card registration/write and erase commands in its command handler. Commands are line-oriented. Enrollment, deletion, wipe, and card management are command-mode operations; attendance recognition is scan-mode operation. The application must stop scanning before a destructive or enrollment command and resume only after the operation reports success or the operator explicitly cancels.

## Status and attendance output

Human-readable status lines include `READY`, `SCAN_MODE`, and `CMD_MODE`. Structured events include status objects such as `{"type":"status","state":"SCAN_MODE"}` and attendance objects for fingerprint `match`, `unknown`, `low_confidence`, and RFID card events. Match events contain the sensor ID and confidence score; card events contain a normalized UID and encrypted payload result. The Python attendance processor converts these events into application outcomes, applies its configured confidence threshold and cooldown, and writes accepted records to SQLite.

The device-side fingerprint cooldown is 2000 ms and the RC522 card cooldown is 1500 ms. These are separate from the desktop cooldown in `settings.json`.

## Synchronization rules

The sensor template ID and the SQLite student row must agree before a matched scan is meaningful. Enrollment therefore has two durable outcomes: the fingerprint template on the sensor and the student metadata in SQLite. Deleting a student removes the sensor template when possible and preserves historical attendance by assigning retained rows to the reserved unregistered identity. A full wipe clears sensor templates and coordinates local data cleanup only after the device operation succeeds. Backup and restore apply to SQLite, not to sensor templates; after restoring a database, verify device IDs before scanning.

## Device discovery

The Python discovery layer enumerates serial ports, probes likely devices, recognizes valid DSIS identity/handshake responses, and records the selected port. Stale saved-port settings can be forgotten from the application. A connected device is not inferred solely from the presence of a COM port; the handshake and protocol response are the meaningful checks.

## Firmware boundary

The firmware does not know student names, roles, permissions, attendance cooldowns, or SQLite state. It reports sensor results and device state. Those application policies belong to Python, which is why changes to firmware output must be accompanied by parser tests and protocol documentation updates.
