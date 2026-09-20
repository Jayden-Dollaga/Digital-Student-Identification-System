# DSIS Hardware Reference

> **Document status:** Current v3 hardware reference  
> **Verified target:** ESP32 WROOM-32 + AS608 fingerprint sensor

## 1. Hardware architecture

DSIS uses the ESP32 as the **device controller and PC serial bridge**. The AS608 performs fingerprint acquisition and template matching. The Windows application does not communicate directly with the sensor; communication passes through the ESP32 firmware.

```text
Windows PC
   │
   │ USB / Serial 115200
   ▼
ESP32 WROOM-32
   │
   │ UART2 / 57600
   ▼
AS608 Fingerprint Sensor
```

This separation is important: a problem can originate at the PC/USB layer, ESP32/firmware layer, or sensor/UART layer.

## 2. Recommended hardware

| Component | Requirement / purpose |
| --- | --- |
| ESP32 WROOM-32 | Maintained controller target |
| AS608 | Fingerprint sensor |
| USB data cable | Power and PC serial communication |
| Breadboard / jumper wires | Temporary sensor interconnection |
| Stable regulated supply | Required according to the exact AS608 module revision |
| Windows PC | Runs DSIS v3 and stores local data |

### Board selection

For the verified firmware target, Arduino IDE uses:

**Tools → Board → ESP32 Arduino → ESP32 Dev Module**

Do not assume another ESP32 family member has identical GPIO, USB, UART, or power behavior.

## 3. Maintained wiring

| AS608 pin | ESP32 connection | Function |
| --- | --- | --- |
| **TX** | GPIO14 / UART2 RX | Sensor → ESP32 data |
| **RX** | GPIO27 / UART2 TX | ESP32 → sensor data |
| **GND** | GND | Common reference |
| **V+** | Appropriate regulated supply | Sensor power |

### UART direction

Serial lines are crossed:

```text
AS608 TX ───────────► ESP32 GPIO14 (RX)
AS608 RX ◄─────────── ESP32 GPIO27 (TX)
AS608 GND ─────────── ESP32 GND
AS608 V+  ─────────── Appropriate sensor supply
```

These GPIO assignments are part of the maintained firmware contract. Changing them in hardware without changing the firmware will break communication.

## 4. Power warning

**Do not assume every AS608 breakout board has identical power circuitry.** Some modules contain regulation or level-shifting circuitry while others may not.

Before powering a sensor:

1. Identify the exact module/revision.
2. Check its label and datasheet.
3. Confirm the required supply voltage.
4. Confirm the logic-level requirements.
5. Use a stable supply.

A generic claim such as "AS608 always uses 3.3 V" or "AS608 always uses 5 V" is unsafe because breakout implementations differ.

## 5. Serial configuration

There are **two separate serial links** in DSIS:

| Link | Rate | Configured by | Purpose |
| --- | ---: | --- | --- |
| PC ↔ ESP32 | **115200 baud** | Desktop application + firmware | Commands, device identity, events |
| ESP32 ↔ AS608 | **57600 baud** | Firmware | Fingerprint sensor protocol |

The Windows application does **not** configure the AS608 baud rate directly.

## 6. Device protocol

The maintained firmware exposes commands including:

| Command | Purpose |
| --- | --- |
| `ID?` | Device identity / handshake |
| `SCAN` | Enter fingerprint scan mode |
| `STOP` | Leave scan mode |
| `ENROLL` | Begin enrollment |
| `DELETE` | Delete a fingerprint template |
| `WIPE` | Clear fingerprint/device identification data |
| `LIST` | Report stored fingerprint information |

The firmware emits JSON events and retains compatibility text messages consumed by existing parsers.

See [v3 System Architecture](../Architecture/v3-system.md) for the complete runtime flow.

## 7. Connection sequence

A healthy startup should look like:

```text
ESP32 powered
      │
      ▼
Windows creates COM port
      │
      ▼
DSIS discovers candidate ports
      │
      ▼
DSIS sends identity probe
      │
      ▼
Firmware returns valid DSIS identity
      │
      ▼
Connection accepted
      │
      ▼
Fingerprint count requested
      │
      ▼
Ready for scan/enrollment
```

A COM port existing by itself does **not** prove that the correct DSIS firmware is running. The application uses device identity information before accepting a connection.

## 8. Wiring quality

For reliable UART communication:

- keep jumper wires short where practical;
- avoid loose breadboard contacts;
- use a stable power source;
- keep signal wiring away from noisy power wiring when possible;
- avoid repeatedly bending or stressing jumper connections;
- verify TX/RX direction before troubleshooting software.

Intermittent wiring can appear as software symptoms such as timeouts, corrupted serial lines, missing events, or random disconnects.

## 9. Pre-flight checklist

Before software troubleshooting, verify:

- [ ] ESP32 powers on.
- [ ] AS608 receives the correct supply.
- [ ] AS608 TX reaches ESP32 GPIO14.
- [ ] AS608 RX reaches ESP32 GPIO27.
- [ ] Grounds are connected.
- [ ] USB cable supports data.
- [ ] Windows shows a serial/USB device.
- [ ] Correct ESP32 board target is selected.
- [ ] Maintained firmware was uploaded successfully.
- [ ] Arduino Serial Monitor is closed before DSIS connects.

## 10. Hardware troubleshooting matrix

| Symptom | Likely layer | First checks |
| --- | --- | --- |
| No COM port | USB/driver/cable | Cable, Device Manager, driver |
| COM port exists but DSIS rejects device | Firmware/protocol | Upload maintained firmware, test `ID?` |
| DSIS connects but fingerprint count fails | ESP32 ↔ AS608 | Power, TX/RX, sensor wiring |
| Sensor repeatedly resets | Power | Supply stability, cable, regulator |
| Scan never produces a match | Sensor/template | Finger placement, enrollment, sensor surface |
| Random disconnects | USB/power/wiring | Cable, USB port, power, jumper quality |
| Upload fails | Bootloader/USB | Board target, COM port, BOOT button, cable |

For detailed recovery procedures, see [Troubleshooting](../Troubleshooting/README.md).

## 11. Firmware source of truth

The maintained firmware is:

`firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino`

Historical sketches under `firmware/` are retained for development history and should not be assumed compatible with the current v3 application.

## 12. Safety and deployment notes

This project is intended for controlled educational deployment. Fingerprint systems involve biometric information; deployment should follow applicable school policies, privacy requirements, access controls, and data-retention rules.

Never publish real student fingerprint records, database backups, credentials, or personal information in the repository.

Last reviewed: 2026-09-20.
