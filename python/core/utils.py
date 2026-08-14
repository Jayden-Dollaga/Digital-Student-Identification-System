###############################################################################
#  utils.py
#  AS608 Fingerprint Attendance System
#
#  Small helper functions used across modules.
###############################################################################

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from config import get_config

CONFIG = get_config()


def parse_json_line(line: str) -> Optional[Dict[str, Any]]:
    if not isinstance(line, str):
        return None
    line = line.strip()
    if not line:
        return None
    # Some serial adapters / FTDI bridges leave a UTF-8 BOM or stray whitespace
    # in front of JSON payloads. Strip the BOM and any surrounding whitespace
    # before parsing so a valid ESP32 match event still reaches the attendance
    # processor in the Qt pipeline.
    line = line.lstrip("\ufeff\t\r\n ")
    if not line.startswith("{"):
        return None
    try:
        parsed = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def get_export_path(filename):
    """
    Build a full export file path inside the exports folder.
    Creates the folder if it doesn't exist.
    Example: get_export_path("attendance_today.xlsx")
    """
    export_folder = CONFIG.export_folder
    export_folder.mkdir(parents=True, exist_ok=True)
    return str(export_folder / filename)


def timestamp_filename(prefix, ext):
    """
    Generate a timestamped filename.
    Example: timestamp_filename("attendance", "xlsx")
             -> "attendance_2026-07-03_12-30-00.xlsx"
    """
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{prefix}_{ts}.{ext}"


def format_datetime(dt):
    """Return a human-readable datetime string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def today_str():
    """Return today's date as YYYY-MM-DD string."""
    return datetime.now().strftime("%Y-%m-%d")


def now_str():
    """Return current time as HH:MM:SS string."""
    return datetime.now().strftime("%H:%M:%S")


def format_attendance_display(record):
    """Return a normalized dictionary for rendering attendance rows in the UI.

    Special-case: `fingerprint_id == 0` denotes an unregistered scan and should
    display as 'Unregistered'.
    """
    fid = record.get('fingerprint_id')
    if fid == 0:
        student_name = 'Unregistered'
    else:
        student_name = record.get("student_name") or f"ID:{fid if fid is not None else 'N/A'}"
    return {
        "fingerprint_id": record.get("fingerprint_id", "N/A"),
        "student_name": student_name,
        "student_no": record.get("student_no", "N/A"),
        "grade": record.get("grade", "N/A"),
        "section": record.get("section", "N/A"),
        "date": record.get("date", "N/A"),
        "time": record.get("time", "N/A"),
        "confidence": record.get("confidence", "N/A"),
        "status": record.get("status", "N/A"),
    }
