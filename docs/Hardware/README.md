# Hardware and Firmware

- [Hardware Connections](hardware-connections.md): component roles and electrical connections.
- [Wiring](wiring.md): confirmed ESP32/AS608 pin mapping.
- [Firmware Variants](firmware-variants.md): maintained all-in-one sketch versus historical sketches.
- [Serial Protocol](serial-protocol.md): commands, status lines, JSON events, baud rates, and synchronization rules.

## Supported path

Use `firmware/ESP32_DSIS_AllInOne/ESP32_DSIS_AllInOne.ino`. The desktop side communicates with the ESP32 at 115200 baud. The ESP32 communicates with the AS608 at 57600 baud on hardware serial pins RX 14 and TX 27 and with the RC522 over SPI. Exact carrier-board power and USB bridge requirements remain board-dependent; follow the wiring guide and verify the board schematic before applying power.

RFID storage is on the card, not in the RC522 reader. The active firmware supports Classic Mini/1K/4K, a 48-byte Type 2 Ultralight profile, NTAG215, and NTAG216 through separate block/page paths. Positively identified MIFARE Plus cards are detection-only; Plus SL1 may be indistinguishable from Classic 1K through SAK alone and is not certified. ISO/IEC 14443-4 cards are reported unclassified (DESFire I/O is not enabled); 144-byte Ultralight-family cards remain ambiguous with the installed library. Writes and erase are read back before DSIS updates student metadata. Existing cards using the previous XOR format must be registered again. See the [serial protocol](serial-protocol.md) for memory layouts and family limitations.
