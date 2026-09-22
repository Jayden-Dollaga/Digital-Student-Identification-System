# Serial and Device Troubleshooting

## Device is not detected

1. Check the USB data cable.
2. Check Device Manager for a COM port.
3. Close Arduino Serial Monitor and other serial terminals.
4. Use DSIS auto-detection.
5. Confirm 115200 baud on the PC side.
6. Review the serial troubleshooting panel and logs.

## Saved port is stale

`data/settings.json` may retain a port from an earlier USB connection. The current connection layer detects when the saved port is no longer enumerated and can fall back to discovery.

Do not delete the whole settings file as the normal serial recovery procedure.

## Access denied

A COM-port access error often means another process owns the port. Close serial monitors/terminals and retry.

## Handshake failure

The discovery layer accepts only the DSIS device identifier:

    Digital Student Identification System

and a protocol version >= 1.

The firmware prints identity JSON during boot and also responds to `ID?`. Discovery checks boot output first, which allows it to identify a reachable device even if the firmware later stalls during AS608 initialization.

## Unexpected device reset

Automatic serial open/reconnect deliberately avoids asserting DTR/RTS before opening the port. The explicit `reset_device` method is the intentional reboot path.

## Scan/enrollment mode conflict

Use `STOP` to return the firmware to command mode before starting the other operation. The v3 API also prevents incompatible mode transitions.
