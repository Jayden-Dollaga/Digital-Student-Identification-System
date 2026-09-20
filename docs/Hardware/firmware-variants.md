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

Enrollment:

1. selects the next available ID when `ENROLL` is used;
2. accepts explicit IDs 1-127 with `ENROLL:<id>`;
3. captures the first fingerprint image;
4. asks for the finger to be removed;
5. captures the same finger again;
6. creates the fingerprint model;
7. stores the model in the selected ID.

If the two captures do not match, enrollment reports a mismatch and the device does not store the new template.

During enrollment, `STOP` cancels the operation and returns the firmware to command mode.

## Scanning behavior

The firmware:

1. waits for a finger;
2. captures the image;
3. converts the image to a template;
4. searches the sensor database;
5. emits a match, unknown, or low-confidence event;
6. applies the firmware's 2-second post-scan delay before another scan cycle.

The current firmware-level minimum confidence is **50**. The desktop application independently classifies matches using its configurable `min_confidence` setting (default 100) as either `GOOD MATCH` or `WEAK MATCH`.

A weak application classification is still a recorded scan; the current attendance processor does not reject it solely because it is below 100. This distinction is important when interpreting attendance data.

## Deletion fix

The maintained firmware calls `loadModel()` before `deleteModel()` so an absent fingerprint slot does not incorrectly report a successful deletion on sensor/library combinations that return an overly permissive delete result.

## LED states

The onboard LED is used as a local device-status indicator. The current sketch defines states for boot, ready, scan, success, enrollment, firmware, error, database error, communication error, host connected, host disconnected, and sleep.

The LED is informational; the PC should use the serial/device state as the authoritative connection signal.

## Historical firmware

| Path | Status |
| --- | --- |
| `firmware/attendance/attendance.ino` | Historical attendance-only sketch |
| `firmware/enroll/enroll.ino` | Historical standalone enrollment utility |
| `firmware/delete/delete.ino` | Historical standalone deletion/list/wipe utility |
| `firmware/test/fingerprint_check/fingerprint_check.ino` | Manual sensor/UART troubleshooting sketch |
| `firmware/prebuilt/attendance_v1.0.bin` | Placeholder, not a verified binary |

The placeholder file contains `BIN_PLACEHOLDER` and must not be flashed.

Use the all-in-one firmware for the supported v3 application workflow.

Last reviewed: 2026-09-20.
