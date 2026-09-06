from __future__ import annotations


import os
import sys
from typing import List


def build_serial_troubleshooting_message(ports: List[str] | None = None) -> str:
    """Return a user-friendly message for serial-connection issues."""
    ports_text = ", ".join(ports or ["no COM ports detected"])
    return (
        "ESP32 not detected.\n"
        f"Detected ports: {ports_text}\n\n"
        "Try these steps in order:\n"
        "1. Plug the ESP32 in with the correct USB cable and press the EN/RST button once.\n"
        "2. Open Device Manager and look for a COM port under 'Ports (COM & LPT)' or 'USB Serial Device'.\n"
        "3. If you see 'CP210x' or 'CH340' drivers missing, install the USB-to-serial driver for the board.\n"
        "4. If the port is still missing, unplug and reconnect the board, then click Refresh.\n"
        "5. Try a different USB cable or port, especially on laptops with power-saving USB hubs.\n"
        "6. If this is a new board, make sure the ESP32 board package is installed in Arduino IDE or the board manager."
    )


def build_common_port_candidates(existing_ports: List[str] | None = None) -> List[str]:
    """Return a list of common COM ports to try, including any detected ones."""
    seen = set()
    ordered = []
    for port in ["COM1", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "COM10", "COM11", "COM12"]:
        if port not in seen:
            seen.add(port)
            ordered.append(port)
    for port in existing_ports or []:
        if port not in seen:
            seen.add(port)
            ordered.append(port)
    return ordered


def open_device_manager() -> None:
    """Open Windows Device Manager."""
    if sys.platform.startswith("win"):
        os.startfile("devmgmt.msc")


def open_driver_help() -> None:
    """Open the ESP32 driver help page in the default browser."""
    if sys.platform.startswith("win"):
        # Use webbrowser module instead of shell command to avoid shell injection risk
        import webbrowser
        webbrowser.open("https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers")
