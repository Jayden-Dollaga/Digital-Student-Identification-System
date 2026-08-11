# Installation and Daily-Use Guide

## Overview

This guide is written for beginners and covers the full workflow for using the Fingerprint Attendance System on a Windows PC without opening Arduino IDE every day.

The main idea is simple:

1. **Upload the ESP32 firmware once** using Arduino IDE.
2. **Run the Python app daily** using [run_qt_gui.bat](../run_qt_gui.bat) or the command line.
3. **Keep the Arduino Serial Monitor closed** while the app is running so the COM port is available.

---

## 1. One-Time Setup: Upload the Firmware

### 1.1 Prepare the hardware

Before uploading firmware, make sure:

- the ESP32 board is connected to the PC with a USB cable,
- the fingerprint sensor is wired correctly,
- the Arduino IDE is installed,
- the ESP32 board URL and the Adafruit Fingerprint library have already been added in Arduino IDE.

### 1.2 Open the correct firmware file

Open the file [firmware/attendance/attendance.ino](firmware/attendance/attendance.ino) in Arduino IDE.

This is the main attendance sketch used for normal daily scanning.

If you are using the desktop app and want a quick first-time check, open the Settings dialog and use the ESP32 Firmware Helper section. It will show whether a bundled firmware binary was detected and, when esptool is available, can attempt an upload using the selected COM port.

### 1.3 Select the correct board

In Arduino IDE, go to:

- **Tools > Board > ESP32 Arduino**
- Choose **ESP32 Dev Module**

This is the recommended board selection for this project.

### 1.4 Recommended upload settings

Use these settings when uploading:

- **Upload Speed:** 115200
- **Flash Frequency:** 40MHz
- **Flash Mode:** QIO
- **Partition Scheme:** Default 4MB with spiffs
- **Core Debug Level:** None

If upload fails, try **115200** first. If your machine is stable, **460800** can also work, but **115200** is the safest default for beginners.

> Warning: Do not change the board type to a random ESP32 variant unless you know the exact hardware model. Use **ESP32 Dev Module** unless you have a specific reason to do otherwise.

### 1.5 Choose the correct COM port

In Arduino IDE, go to:

- **Tools > Port**

Choose the COM port that belongs to the ESP32.

A quick way to find it:

1. Open **Device Manager**.
2. Expand **Ports (COM & LPT)**.
3. Look for an ESP32, CP210x, or USB Serial device.
4. Select that port in Arduino IDE.

If you do not see a COM port, the driver may not be installed correctly.

### 1.6 Upload the sketch

Click **Upload**.

When it finishes successfully, you should see a message similar to **Done uploading**.

### 1.7 What to do after a successful upload

After the upload completes:

- leave the ESP32 connected to the PC,
- keep the Arduino Serial Monitor **closed**,
- open the Python app next.

> Important: The Serial Monitor and the Python app cannot both use the same COM port at the same time.

---

## 2. Daily Operation: Run Without Arduino IDE

### 2.1 Launch the app with the provided batch file

From the project root, double-click [run_qt_gui.bat](../run_qt_gui.bat).

This is the easiest way to start the app for everyday use.

If you need the legacy CustomTkinter interface, use [run_app.bat](run_app.bat) instead.

### 2.2 Alternative: launch from the command line

You can also open a terminal in the project root and run the legacy GUI:

```powershell
python python/gui/app.py
```

or the modern Qt UI:

```powershell
python .\run_qt_gui.py
```

### 2.2.1 Recommended Qt startup

The Qt UI is recommended for newer installs because it avoids the `Pillow` dependency, supports theme switching, and includes an auto-discover option for ESP32 COM ports.

```powershell
run_qt_gui.bat
```

> Note: If `python -m pip install Pillow` fails on Python 3.14, use Python 3.13 for the legacy GUI or use the Qt UI with `python .\run_qt_gui.py` instead.

### 2.2.1 Run it again

When you want to start the app again, use the same commands from the project root:

```powershell
.\run_qt_gui.bat
```

Or run the Qt UI directly:

```powershell
python .\run_qt_gui.py
```

If you already installed dependencies once, you do not need to reinstall them before each launch.

### 2.3 Create a desktop shortcut

For daily convenience, create a shortcut to [run_qt_gui.bat](../run_qt_gui.bat):

1. Right-click [run_qt_gui.bat](../run_qt_gui.bat).
2. Choose **Create shortcut**.
3. Move the shortcut to your Desktop.
4. Double-click it whenever you want to start the system.

If you want, you can also pin the shortcut to the taskbar.

### 2.4 Expected normal startup behavior

When the app starts normally, you should see:

- the desktop GUI open,
- the app connect to the ESP32 successfully,
- the status change to connected,
- the system wait for fingerprint input.

If the firmware is running correctly, the ESP32 will also be ready to respond to scan, enroll, and wipe commands.

---

## 3. Important Configuration

### 3.1 Default baud rate

The default baud rate for the ESP32 communication is **115200**.

This is configured in [python/config.py](python/config.py).

### 3.2 Change the COM port and baud rate

You can change the COM port and baud rate in the app through the settings UI or by editing configuration values in [python/config.py](python/config.py).

The app also saves user choices in the app's settings storage under [data](data).

### 3.3 Where settings are saved

The application stores its saved settings in the [data](data) folder so your preferred COM port and UI choices persist between launches.

---

## 4. Driver and Hardware Requirements

### 4.1 USB-to-UART driver

Many ESP32 boards use a **CP210x** or similar USB-to-UART chip.

If you do not see a COM port, install the correct driver first.

Common driver families include:

- **CP210x** driver
- **CH340/CH341** driver (if your board uses that chip)

If you are unsure, check the board label or the USB chip on the ESP32 board.

### 4.2 Correct wiring reference

The fingerprint sensor should be wired so that:

- **V+** goes to power,
- **GND** goes to ground,
- **TX** and **RX** are cross-connected properly.

The project’s main firmware in [firmware/attendance/attendance.ino](firmware/attendance/attendance.ino) expects the sensor and ESP32 to be connected in the correct serial arrangement.

### 4.3 Power requirements

Use a reliable USB connection.

If the ESP32 is unstable, try:

- a different USB cable,
- a different USB port,
- a direct connection to the PC instead of a USB hub.

> Warning: Weak or unstable power can cause the ESP32 to disconnect randomly or fail to respond.

---

## 5. Comprehensive Troubleshooting

### 5.1 No COM ports appear in the app

Try these steps:

1. Confirm the ESP32 is plugged in.
2. Check **Device Manager** for a COM port.
3. Reinstall the USB driver if needed.
4. Try another USB cable or USB port.
5. Close Arduino IDE if it still has the serial port open.

### 5.2 App connects but the sensor does not respond

This usually means the firmware or wiring is not correct.

Check:

1. The sensor is powered.
2. TX/RX are cross-connected correctly.
3. The ESP32 firmware uploaded successfully.
4. The sensor is not loose or disconnected.

### 5.3 "Failed to connect" or timeout errors

Common causes:

- the wrong COM port is selected,
- the board is not actually running the firmware,
- the serial monitor is still open,
- the USB cable is loose or bad.

Try:

1. Reconnect the board.
2. Re-select the COM port.
3. Restart the app.
4. Re-upload the firmware if needed.

### 5.4 Fingerprint scans are not detected

If the app does not detect a fingerprint:

1. Make sure the finger is placed firmly and slowly.
2. Clean the sensor surface.
3. Try a different finger.
4. Re-enroll the fingerprint if necessary.
5. Confirm the firmware is still running and the board has not disconnected.

### 5.5 Enrollment or wipe commands do not work

If enrollment or wipe fails:

1. Confirm the app is connected to the correct COM port.
2. Check that the ESP32 firmware is still running.
3. Confirm the board is not resetting.
4. Try the action again after restarting the app.

### 5.6 Baud rate mismatch issues

If the app appears to connect but behaves strangely:

1. Verify the baud rate is **115200**.
2. Make sure the firmware and app are using the same rate.
3. Re-upload the firmware if the setting changed unexpectedly.

### 5.7 USB port keeps disconnecting

Try:

1. A better USB cable.
2. A direct USB port on the computer.
3. Avoiding powered USB hubs.
4. Checking whether the board is drawing too much power from a weak source.

---

## 6. Best Practices and Tips

### 6.1 Safely restart the system

When something seems wrong:

1. Close the app.
2. Disconnect and reconnect the ESP32.
3. Reopen the app.
4. Recheck the COM port.

### 6.2 Check logs when something goes wrong

The project writes logs to the [data](data) folder. If the app is not behaving properly, open the most recent log file and look for connection, scan, or enrollment messages.

### 6.3 Verify the firmware is running correctly

A healthy ESP32 should:

- appear on a COM port,
- connect to the Python app,
- respond to fingerprint input,
- send scan results back to the app.

If the system does not respond after upload, the firmware may not have been flashed correctly or the board may need to be reset.

### 6.4 Keep the Serial Monitor closed during normal use

This is one of the most common beginner mistakes.

If the Serial Monitor is open, the Python app may fail to access the COM port.

---

## Quick Summary

For daily use:

1. **Upload the firmware once** using [firmware/attendance/attendance.ino](firmware/attendance/attendance.ino).
2. **Use [run_qt_gui.bat](../run_qt_gui.bat)** to launch the app.
3. **Keep the Serial Monitor closed**.
4. **Use the correct COM port and 115200 baud rate**.
5. **Restart the app if the sensor stops responding**.
