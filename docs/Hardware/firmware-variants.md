# Firmware Variants

DSIS contains one maintained firmware sketch and several historical utilities. The sketches use an ESP32 with an AS608 fingerprint sensor on UART2, with sensor TX connected to GPIO14 and sensor RX connected to GPIO27.

## Supported Workflow

Use [ESP32_Fingerprint_AllInOne.ino](../../firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino) for the current DSIS application. It combines enrollment, deletion, wipe, listing, and attendance scan modes, so it is flashed once and controlled by serial commands. The Qt application communicates with this protocol.

## Historical Sketches

| Sketch | Purpose | Status |
| --- | --- | --- |
| `firmware/attendance/attendance.ino` | Older attendance-only scanner using the earlier text protocol | Historical compatibility; not the primary DSIS firmware |
| `firmware/enroll/enroll.ino` | Standalone serial enrollment utility | Historical utility; use `ENROLL` through the all-in-one sketch for DSIS |
| `firmware/delete/delete.ino` | Standalone deletion/list/wipe utility | Historical utility; use `DELETE`, `LIST`, and `WIPE` through the all-in-one sketch |
| `firmware/test/fingerprint_check/fingerprint_check.ino` | Manual sensor and UART test | Hardware troubleshooting only |
| `firmware/prebuilt/attendance_v1.0.bin` | Placeholder file bundled by the legacy portable spec | Not a verified firmware image; do not flash |

The older sketches should not be mixed with the current host protocol without verifying their serial output and command format.

## Flashing Guidance

Upload the all-in-one `.ino` sketch with Arduino IDE for a source build. Keep the Python application and Arduino Serial Monitor from opening the same COM port simultaneously. The current host default baud rate is 115200; the sensor UART is configured separately by the firmware.

The file named `attendance_v1.0.bin` is retained as an historical placeholder.
Git records its content as the literal text `BIN_PLACEHOLDER`, not a compiled
binary. No source sketch, compiler version, board setting, or upload procedure
can be established from repository history. It must not be flashed.

Its current SHA-256 is:

```text
D990B199010D6DA7875876DBC40A1D7FC848201719FA5BF66BB7FA8B77F097F1
```

<!-- TODO: verify — ask project owner whether this placeholder should be replaced and which source built the intended binary. -->

Last verified: 2026-09-03, against commit d68a405
