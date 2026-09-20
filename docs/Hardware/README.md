# Hardware and Firmware

- [Hardware Connections](hardware-connections.md): component roles and electrical connections.
- [Wiring](wiring.md): confirmed ESP32/AS608 pin mapping.
- [Firmware Variants](firmware-variants.md): maintained all-in-one sketch versus historical sketches.
- [Serial Protocol](serial-protocol.md): commands, status lines, JSON events, baud rates, and synchronization rules.

## Supported path

Use `firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino`. The desktop side communicates with the ESP32 at 115200 baud. The ESP32 communicates with the AS608 at 57600 baud on hardware serial pins RX 14 and TX 27. Exact carrier-board power and USB bridge requirements remain board-dependent; follow the wiring guide and verify the board schematic before applying power.
