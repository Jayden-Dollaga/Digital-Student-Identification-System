# Hardware Connections

## Overview

The Digital Student Identification System (DSIS) uses an ESP32 board and an AS608 optical fingerprint sensor. The ESP32 acts as the controller and serial bridge, while the AS608 provides scanning and matching functionality.

## Recommended hardware

- ESP32 WROOM-32 board selected as **ESP32 Dev Module**
- AS608 fingerprint sensor module
- USB cable for power and serial communication
- breadboard and jumper wires
- suitable regulated power for the exact AS608 module revision

## Default wiring

| AS608 pin | Connection | ESP32 connection |
| --- | --- | --- |
| V+ | Module power input | Use the voltage specified by the sensor board revision; the verified setup uses the shield's regulated sensor supply. |
| GND | Ground | GND |
| TX | Sensor TX | ESP32 GPIO14 (UART2 RX) |
| RX | Sensor RX | ESP32 GPIO27 (UART2 TX) |

> TX and RX are crossed. These GPIO assignments are specific to the maintained firmware in [ESP32_Fingerprint_AllInOne.ino](../../firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino); do not change them without changing the firmware.
> AS608 modules and breakout boards do not all have the same power circuitry. Check the label or datasheet for your revision before applying power. Do not assume that an unregulated sensor board can be connected directly to 3.3V or 5V.

## Notes on wiring quality

- use short, secure jumper connections
- keep the sensor away from power noise where possible
- avoid loose wires that can cause intermittent serial reads
- make sure the sensor board is powered from a stable source

## Serial considerations

The host machine connects to the ESP32 through USB at **115200 baud**. The internal ESP32-to-AS608 UART runs at **57600 baud**. The Python application only configures the host-side rate and uses the discovered COM port. COM numbers are assigned by Windows and vary between machines.

## Validation checklist

Before using the device, confirm that:

- the ESP32 powers on normally
- the sensor powers on and stays stable
- the USB cable is reliable
- the serial port appears in the operating system
- the firmware uploads successfully
