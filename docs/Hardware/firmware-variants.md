# DSIS Firmware and Hardware Variants

## Current firmware

The maintained firmware is:

`firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino`

It is a single all-in-one sketch intended to remain flashed on the ESP32 while DSIS switches between device operations.

Current firmware metadata embedded in the sketch:

| Field | Value |
| --- | --- |
| Device identifier | Digital Student Identification System |
| Board | ESP32 |
| Firmware | 1.0.10 |
| Sensor | AS608 |
| Protocol | 1 |
| Host baud | 115200 |
| Sensor UART baud | 57600 |
| Fingerprint ID range | 1-127 |

## Supported commands

| Command | Purpose |
| --- | --- |
| `ID?` | Return device identity metadata |
| `SCAN` | Enter fingerprint attendance scan mode |
| `STOP` | Leave scan mode and return to command mode |
| `LIST` | Report the number of stored fingerprint templates |
| `ENROLL` | Enroll using the next free fingerprint ID |
| `ENROLL:<id>` | Enroll into a specific ID from 1-127 |
| `DELETE:<id>` | Delete a specific fingerprint template |
| `WIPE` | Delete all stored fingerprint templates |
| `STATUS:<state>` | Accept host status information for the firmware LED state |
| JSON status | Accept a status object containing `type=status` and `state` |

Commands are line-oriented and handled on the ESP32 host serial port.

## Firmware events

The firmware emits human-readable compatibility messages and structured JSON.

Examples:

```json
{"device":"Digital Student Identification System","board":"ESP32","firmware":"1.0.10","sensor":"AS608","protocol":1,"serial_number":"..."}
```

```json
{"type":"status","state":"SCAN_MODE"}
```

```json
{"type":"attendance","event":"match","id":1,"confidence":223}
```

```json
{"type":"attendance","event":"unknown"}
```

```json
{"type":"attendance","event":"low_confidence","confidence":42}
```

## Enrollment behavior

Enrollment selects the next available ID when `ENROLL` is used, or accepts explicit IDs 1-127 with `ENROLL:<id>`. The sensor captures the same finger twice, creates a model, and stores it in the selected slot. A mismatch does not store the new template. `STOP` cancels enrollment and returns to command mode.

## Scanning behavior

The firmware waits for a finger, captures and converts the image, searches the sensor database, emits a match/unknown/low-confidence event, and applies a 2-second firmware-level post-scan delay.

The firmware-level minimum confidence is **50**. The desktop application independently classifies matches using its configurable `min_confidence` setting (default 100). A weak application classification is still recorded by the current attendance processor.

## Deletion behavior

The maintained firmware loads the selected fingerprint model before deleting it, avoiding false-success behavior on sensor/library combinations that are permissive about deleting an absent slot.

## LED states

The onboard LED indicates boot, ready, scan, success, enrollment, firmware, error, database error, communication error, host connection, host disconnection, and sleep states. The PC should use serial/device state as the authoritative connection signal.

## Historical firmware

| Path | Status |
| --- | --- |
| `firmware/attendance/attendance.ino` | Historical attendance-only sketch |
| `firmware/enroll/enroll.ino` | Historical standalone enrollment utility |
| `firmware/delete/delete.ino` | Historical standalone deletion/list/wipe utility |
| `firmware/test/fingerprint_check/fingerprint_check.ino` | Manual sensor/UART troubleshooting sketch |

No verified prebuilt firmware binary is distributed by the current repository. Do not treat an old placeholder or generated artifact as a flashable release image; use the maintained all-in-one source sketch for the supported v3 workflow.

Use the all-in-one firmware for the supported v3 application workflow.

Last reviewed: 2026-09-20.
