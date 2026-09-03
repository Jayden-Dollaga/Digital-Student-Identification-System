# Troubleshooting DSIS

## No COM Port Appears

1. Connect the ESP32 with a data-capable USB cable.
2. Open **Device Manager > Ports (COM & LPT)**.
3. Install the driver matching the USB bridge shown there. CP210x, CH340/CH341, CH9102, and FTDI boards use different drivers. See the [USB Serial Drivers section](UserGuide/installation-guide.md#41-usb-serial-driver).
4. Try another USB port and reconnect the board.

Python packages do not install Windows USB drivers. Native-USB ESP32 boards may expose USB CDC or USB-JTAG instead of a COM port; those variants are not verified by this project.

## Access Denied on a COM Port

The selected COM port is already open in another application. COM numbers such as COM4 are examples and vary by computer.

Close Arduino IDE, Arduino Serial Monitor, PuTTY, Tera Term, other serial terminals, other DSIS instances, and Python processes that may use the port. Disconnect and reconnect the board, then try again. Windows does not provide a dependable built-in mapping from an open COM handle to its owning process; use a trusted handle-inspection utility if the port remains locked.

## Firmware Upload Fails

- Select **ESP32 Arduino > ESP32 Dev Module** for the verified ESP32 WROOM-32 target.
- Select the COM port currently assigned to the board.
- Use an upload speed of **115200**.
- Try a different data cable or USB port.
- Press and hold the board's **BOOT** button while upload begins if the board does not enter download mode.

Upload the maintained [all-in-one firmware](../firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino). The historical sketches and `firmware/prebuilt/attendance_v1.0.bin` placeholder are not interchangeable with the desktop application.

## App Connects but Sensor Does Not Respond

Check the sensor power and crossed UART wiring:

- AS608 TX to ESP32 GPIO14 (UART2 RX)
- AS608 RX to ESP32 GPIO27 (UART2 TX)
- GND to GND
- V+ connected according to the exact sensor module revision

The PC-to-ESP32 connection uses **115200 baud**. The internal ESP32-to-AS608 connection uses **57600 baud** and is configured by the firmware, not in the desktop app.

## Test the Host Serial Connection

Run this from the project root after closing the DSIS application and all serial monitors:

```python
import serial

port = "COM5"  # Replace with the port shown by Device Manager.
try:
    with serial.Serial(port, 115200, timeout=2) as connection:
        connection.write(b"ID?\n")
        print(connection.readline())
except PermissionError as error:
    print(f"Port is already in use: {error}")
except Exception as error:
    print(f"Serial test failed: {error}")
```

The application can auto-discover a device when Windows exposes a COM port and the firmware responds to the DSIS identity handshake. In the Qt app, click **Connect** and use auto-discovery or select the detected port manually.

## Collect Diagnostics

From the project root, run:

```powershell
python -c "from python.core.device_discovery import list_serial_ports; print(list_serial_ports())"
```

When reporting a problem, include the output, the Device Manager device name, the selected board, the USB bridge family, and the relevant lines from `data/logs/fingerprint_attendance.log`.
