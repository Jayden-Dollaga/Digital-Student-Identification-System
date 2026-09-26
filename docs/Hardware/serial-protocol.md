# ESP32 Serial Protocol

This is the current protocol implemented by the all-in-one ESP32 sketch and consumed by the Python serial layer.

## Links and baud rates

| Link | Baud | Owner |
| --- | ---: | --- |
| DSIS desktop to ESP32 USB serial | 115200 | `serial_handler.py` and firmware `Serial` |
| ESP32 to AS608 UART | 57600 | firmware `HardwareSerial(2)` and `Adafruit_Fingerprint` |

The desktop must not use the sensor baud rate directly.

After discovery validates the DSIS identity and protocol through `ID?`, the
Python host sends `{"type":"status","state":"HOST_CONNECTED"}`. The
firmware accepts destructive commands only while this host-connected state is
active. `HOST_DISCONNECTED` clears the state. This is a protocol gate, not a
cryptographic secret for someone with direct USB serial access.

## Host commands

The active firmware accepts `ID?`, `SCAN`, `STOP`, `ENROLL`, `ENROLL:<id>`, `DELETE:<id>`, `WIPE`, and `LIST`. RFID commands include `CARD_WRITE_HEX:<96 hex chars>` for registration and `CARD_ERASE` for one-tap clearing of card data. Both write and erase operate only on MIFARE Classic 1K data blocks 4-6; the sector trailer and access keys are never overwritten. Each block is written and read back, and a `card_write` event reports success only when every byte matches. Unsupported, unreadable, or unwritable tags must not be treated as registered. Commands are line-oriented. The application stops normal scanning for card management and updates the student-to-card link only after verified write success.

RFID registration supports writable MIFARE Classic 1K cards read by the RC522. MIFARE Ultralight and Ultralight C use a different page-based protocol and are reported as unsupported. The reader has no 1 KB storage of its own. The 48-byte card payload contains a format version, a random 12-byte nonce, and AES-GCM ciphertext plus its authentication tag. The encrypted plaintext carries the fingerprint ID and a length-prefixed student number (up to 17 UTF-8 bytes). The normalized card UID is authenticated as associated data. A fresh AES-256 key is generated and kept separately from legacy keys in the ignored application data directory (`data/settings.json`). Cards written with the former XOR format are not accepted and must be re-registered.

## Status and attendance output

Human-readable status lines include `READY`, `SCAN_MODE`, and `CMD_MODE`. Structured events include status objects such as `{"type":"status","state":"SCAN_MODE"}` and attendance objects for fingerprint `match`, `unknown`, `low_confidence`, and RFID card events. Match events contain the sensor ID and confidence score; card events contain a normalized UID and the 96-character encrypted payload. The Python attendance processor accepts a card only when the payload authenticates for that UID and its fingerprint ID/student number agree with the linked database record. Unknown or unreadable cards remain distinguishable from unknown fingerprints.

The device-side fingerprint cooldown is 2000 ms. RFID polling does not block for a fixed cooldown; a card is halted after each operation, and a pending write wakes the same UID again if it remains on the reader. This is separate from the desktop attendance cooldown in `settings.json`.

## Synchronization rules

The sensor template ID and the SQLite student row must agree before a matched scan is meaningful. Enrollment therefore has two durable outcomes: the fingerprint template on the sensor and the student metadata in SQLite. Deleting a student removes the sensor template when possible and preserves historical attendance by assigning retained rows to the reserved unregistered identity. A full wipe clears sensor templates and coordinates local data cleanup only after the device operation succeeds. Backup and restore apply to SQLite, not to sensor templates; after restoring a database, verify device IDs before scanning.

## Device discovery

The Python discovery layer enumerates serial ports, probes likely devices, recognizes valid DSIS identity/handshake responses, and records the selected port. Stale saved-port settings can be forgotten from the application. A connected device is not inferred solely from the presence of a COM port; the handshake and protocol response are the meaningful checks.

## Firmware boundary

The firmware does not know student names, roles, permissions, attendance cooldowns, or SQLite state. It reports sensor results and device state. Those application policies belong to Python, which is why changes to firmware output must be accompanied by parser tests and protocol documentation updates.
