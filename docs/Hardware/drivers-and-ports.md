# Drivers and Serial Ports

## Serial topology

**PC ↔ ESP32:** 115200 baud

**ESP32 ↔ AS608:** 57600 baud

The PC does not directly communicate with the AS608.

## Discovery workflow

The current discovery layer:

1. enumerates actual Windows COM ports,
2. ranks candidates using descriptors and known USB VID/PID values,
3. considers the preferred/configured port when present,
4. probes candidate ports,
5. validates the DSIS device identifier and protocol version.

The accepted identity is:

    Digital Student Identification System

The minimum supported protocol is 1.

## Boot-aware discovery

The firmware prints identity JSON during boot before AS608 initialization is complete.

The current discovery code reads boot output and validates JSON identity as it arrives. This means a reachable DSIS device that subsequently gets stuck because the AS608 failed can still be identified by the host.

If no valid identity is found in boot output, discovery sends `ID?` and waits for a validated response.

## Stale saved ports

`data/settings.json` stores `com_port` as a connection preference.

If the saved port is no longer present in the current COM-port enumeration, DSIS can clear the stale preference and fall back to discovery.

Operators should not delete `settings.json` as the first serial-recovery step.

## DTR/RTS behavior

Automatic connection/reconnect builds the pyserial object while closed, sets DTR and RTS inactive, then opens the port. This prevents the normal pyserial open edge from unintentionally resetting the ESP32.

The explicit `reset_device` API method intentionally pulses DTR when an administrator requests a device reset.

## Windows checks

When the device cannot be found:

1. verify the USB cable is data-capable,
2. check Device Manager → Ports (COM & LPT),
3. install the driver required by the board's USB interface,
4. close Arduino Serial Monitor and other serial terminals,
5. try DSIS auto-detection,
6. inspect the DSIS serial troubleshooting panel/log.

Common USB bridge families include CP210x, CH34x, and FTDI. The required driver depends on the actual ESP32 board.
