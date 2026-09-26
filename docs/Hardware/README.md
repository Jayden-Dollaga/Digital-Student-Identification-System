# Hardware and Firmware

- [Hardware Connections](hardware-connections.md): component roles and electrical connections.
- [Wiring](wiring.md): confirmed ESP32/AS608 pin mapping.
- [Firmware Variants](firmware-variants.md): maintained all-in-one sketch versus historical sketches.
- [Serial Protocol](serial-protocol.md): commands, status lines, JSON events, baud rates, and synchronization rules.

## Supported path

Use `firmware/ESP32_DSIS_AllInOne/ESP32_DSIS_AllInOne.ino`. The desktop side communicates with the ESP32 at 115200 baud. The ESP32 communicates with the AS608 at 57600 baud on hardware serial pins RX 14 and TX 27 and with the RC522 over SPI. Exact carrier-board power and USB bridge requirements remain board-dependent; follow the wiring guide and verify the board schematic before applying power.

RFID storage is on a writable MIFARE Classic 1K card, not in the RC522 reader. DSIS uses data blocks 4-6 for an authenticated encrypted payload and verifies each block after writing. Existing cards using the previous XOR format must be registered again. See the [serial protocol](serial-protocol.md) for the payload and compatibility details.
