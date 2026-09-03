# Wiring Guide

## ESP32 to AS608

- V+ -> the regulated supply specified for the exact AS608 module revision
- GND -> GND
- TX -> GPIO 14
- RX -> GPIO 27

## Notes

- The PC-to-ESP32 link uses 115200 baud; the internal ESP32-to-AS608 UART uses 57600 baud.
- Check the sensor label or datasheet before applying power. Do not assume every AS608 breakout accepts the same voltage.
- If serial communication is unstable, check cable grounding and power.
