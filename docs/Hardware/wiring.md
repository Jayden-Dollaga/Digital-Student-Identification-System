# DSIS Hardware Wiring Guide

## Verified signal path

```text
AS608 fingerprint sensor
        │
        │ UART 57600
        ▼
ESP32 WROOM-32 / UART2
        │
        │ USB Serial 115200
        ▼
Windows PC / DSIS v3
```

## UART connections

| AS608 signal | ESP32 pin | Function |
| --- | --- | --- |
| TX | GPIO14 | ESP32 UART2 RX |
| RX | GPIO27 | ESP32 UART2 TX |
| GND | GND | Common ground |
| V+ | Appropriate module supply | Sensor power |

TX and RX are intentionally crossed.

## Host connection

The ESP32 is connected to the PC over USB.

| Link | Rate | Configured by |
| --- | ---: | --- |
| PC ↔ ESP32 | **115200 baud** | DSIS / host serial connection |
| ESP32 ↔ AS608 | **57600 baud** | Maintained firmware |

The 57600 sensor rate must not be entered as the PC COM-port baud rate.

## Board target

The documented and verified hardware target is an ESP32 WROOM-32 development board selected as:

**Arduino IDE → ESP32 Arduino → ESP32 Dev Module**

Other ESP32 variants may expose different USB interfaces or require different board settings; native-USB variants are not the project's verified target.

## Power warning

AS608 modules and breakout boards can differ in their voltage-regulation circuitry.

Before connecting V+:

1. Read the exact module label.
2. Confirm the module's allowed supply voltage.
3. Confirm the power source is stable.
4. Do not assume a generic 3.3 V or 5 V connection is safe for every breakout.

The repository documents the signal wiring, but the exact sensor power requirement remains module-revision dependent.

## Wiring checklist

Before powering the device:

- TX → GPIO14
- RX → GPIO27
- GND → GND
- V+ → verified sensor supply
- USB cable connected to the ESP32
- no bent/loose jumper wires
- sensor wiring separated from obvious sources of electrical noise

## Firmware relationship

These GPIO assignments are hard-coded in the maintained firmware:

```cpp
#define FINGERPRINT_RX 14
#define FINGERPRINT_TX 27
```

Changing the wiring without changing the firmware will break sensor communication.

See [hardware-connections.md](hardware-connections.md) for the broader hardware overview and [firmware-variants.md](firmware-variants.md) for the current firmware source.

Last reviewed: 2026-09-20.
