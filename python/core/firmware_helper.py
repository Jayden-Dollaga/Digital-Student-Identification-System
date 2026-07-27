"""Helpers for firmware discovery and simple ESP32 upload guidance."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from config import get_config

CONFIG = get_config()


def discover_firmware_candidates(project_root: Optional[Path] = None) -> List[Path]:
    """Return likely firmware files for the attendance sketch, preferring a prebuilt .bin."""
    root = Path(project_root or CONFIG.project_root)
    candidates: List[Path] = []
    search_roots = [
        root / "firmware" / "attendance",
        root / "firmware",
        root / "dist" / "portable" / "FingerprintAttendanceSystem",
    ]

    for folder in search_roots:
        if not folder.exists():
            continue
        for pattern in ("*.bin", "*.ino", "*.hex"):
            candidates.extend(sorted(folder.rglob(pattern)))

    return sorted({path.resolve() for path in candidates})


def find_firmware_binary(project_root: Optional[Path] = None) -> Optional[Path]:
    """Find a bundled firmware binary if available."""
    for path in discover_firmware_candidates(project_root=project_root):
        if path.suffix.lower() == ".bin":
            return path
    return None


def find_arduino_firmware(project_root: Optional[Path] = None) -> Optional[Path]:
    """Find the main attendance .ino source sketch."""
    root = Path(project_root or CONFIG.project_root)
    path = root / "firmware" / "attendance" / "attendance.ino"
    return path if path.exists() else None


def esptool_available() -> bool:
    return shutil.which("esptool") is not None or shutil.which("esptool.py") is not None


def build_upload_command(port: str, firmware_path: Path, baud_rate: int = 115200) -> List[str]:
    """Create an esptool command for flashing a firmware binary."""
    executable = "esptool.py"
    if shutil.which(executable):
        tool = executable
    elif shutil.which("esptool"):
        tool = "esptool"
    else:
        tool = sys.executable
    command = [tool, "--chip", "esp32", "--port", port, "--baud", str(baud_rate), "write_flash", "-z", "0x1000", str(firmware_path)]
    return command


def upload_firmware(port: str, firmware_path: Optional[Path] = None, baud_rate: int = 115200) -> Tuple[bool, str]:
    """Attempt to upload firmware with esptool if available."""
    path = firmware_path or find_firmware_binary()
    if path is None:
        return False, "No firmware binary was found. Build or bundle a .bin file first."
    if not esptool_available():
        return False, "esptool is not installed. Install it with: pip install esptool"
    # Delegate to the streaming uploader but keep a simple sync API for callers
    ok, out = upload_firmware_with_progress(port, path, baud_rate=baud_rate)
    return ok, out


def upload_firmware_with_progress(
    port: str,
    firmware_path: Optional[Path] = None,
    baud_rate: int = 115200,
    progress_callback=None,
    timeout: int = 600,
) -> Tuple[bool, str]:
    """Upload firmware while streaming output to `progress_callback`.

    `progress_callback` will be called with a single string argument for each output line.
    If `progress_callback` is None this behaves like the previous synchronous uploader.
    """
    path = firmware_path or find_firmware_binary()
    if path is None:
        msg = "No firmware binary was found. Build or bundle a .bin file first."
        if progress_callback:
            progress_callback(msg)
        return False, msg
    if not esptool_available():
        msg = "esptool is not installed. Install it with: pip install esptool"
        if progress_callback:
            progress_callback(msg)
        return False, msg

    command = build_upload_command(port, path, baud_rate=baud_rate)

    try:
        # Use Popen to stream output lines and report progress
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        output_lines = []
        if proc.stdout is not None:
            for line in proc.stdout:
                line = line.rstrip("\n")
                output_lines.append(line)
                if progress_callback:
                    try:
                        progress_callback(line)
                    except Exception:
                        pass
        proc.wait(timeout=timeout)
        out = "\n".join(output_lines).strip()
        if proc.returncode == 0:
            return True, out or "Firmware upload completed."
        return False, out or "Firmware upload failed."
    except Exception as exc:  # pragma: no cover - runtime safety
        msg = str(exc)
        if progress_callback:
            progress_callback(msg)
        return False, msg
