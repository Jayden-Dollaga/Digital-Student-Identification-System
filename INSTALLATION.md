# Installation

The maintained installation and daily-use instructions are in the
[DSIS User Guide](docs/UserGuide/installation-guide.md).

For a quick Windows launch from the repository root:

```text
run_web_gui.bat
```

Install dependencies first with:

```text
python -m pip install -r requirements.txt
```

Before connecting the board, install the Windows driver matching its USB interface chip. CP210x is only for Silicon Labs CP210x boards; other common families are CH340/CH341, CH9102, and FTDI. Identify the chip in **Device Manager > Ports (COM & LPT)**. See the [driver section in the User Guide](docs/UserGuide/installation-guide.md#41-usb-serial-driver) for vendor links and native-USB notes.

The verified target is an ESP32 WROOM-32 selected as **ESP32 Dev Module** in Arduino IDE. Native-USB ESP32 variants are not verified by this project. The active desktop UI is the v3 HTML/pywebview interface; the earlier Qt and CustomTkinter trees are archived snapshots.

See [Troubleshooting](docs/TROUBLESHOOTING.md) for COM-port and firmware checks.

## V3 Workflow Acceptance

The maintained interface is the HTML/pywebview application launched by
`run_web_gui.bat` or `python run_web_gui.py`. After connecting the board,
verify the following sequence:

1. Connect and confirm port, baud, device metadata, and fingerprint count.
2. Start and stop scanning; confirm the device mode and scan button agree.
3. Scan a registered finger and confirm the attendance row and dashboard count update.
4. Start enrollment, cancel it, and confirm the device returns to command mode.
5. Complete enrollment and save the student only after device success is reported.
6. Delete a student and confirm the database changes only after device deletion succeeds.
7. Wipe device fingerprints and confirm the device count reaches zero while student records remain.
8. Disconnect and reconnect the board; confirm pending operations clear and the count refreshes.

V3 roles are local workflow permissions, not account authentication:

| Role | Permissions |
| --- | --- |
| Administrator | Scan, enroll, delete, wipe, export, backup, restore, settings, serial commands |
| Teacher | Scan, export, backup |
| Guest | Scan only |

Hardware verification recorded 2026-09-09: COM4 identified as Digital Student
Identification System / ESP32 / AS608 firmware 1.0, protocol 1. Auto-discovery,
connect, LIST/fingerprint-count traffic, scan mode entry/exit, enrollment
cancellation, disconnect, empty-device wipe, and absent-ID deletion passed.
Valid-finger attendance capture and successful enrollment still require an
operator to place a finger on the sensor.

Last verified: 2026-09-09, source build, packaged startup, automated tests, and
safe physical lifecycle smoke test.
