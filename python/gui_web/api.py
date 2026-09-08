"""pywebview JS<->Python bridge for the v3 (HTML) DSIS interface.

This module is the only place the web UI talks to Python. It wraps the
existing, GUI-agnostic backend (core.database, core.serial_handler,
core.attendance, core.permissions, config, settings_store) the same way
v1 (CustomTkinter) and v2 (Qt) each wrapped it in their own GUI toolkit -
no backend logic is duplicated here, only translated into plain
dict/list/str/bool values that can cross the JS bridge as JSON.

Every public method on Api() is callable from JavaScript as
``pywebview.api.method_name(args...)`` and returns a JSON-serializable
value (or raises, which pywebview turns into a rejected JS promise).
"""

from __future__ import annotations

import csv
import io
import logging
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_config
from core import commands as cmds
from core import database as db
from core import permissions
from core.attendance import AttendanceProcessor
from core.logger import LOG, LOG_FILE, AppFormatter, log
from core.serial_handler import SerialHandler, list_serial_ports
from core.utils import parse_json_line
from settings_store import load_settings, save_settings

CONFIG = get_config()

# Regexes copied verbatim from archive/legacy-ui/v2/python/gui_qt/workers/serial_worker.py
# so enroll/wipe/delete parsing matches the real firmware output exactly.
RE_ENROLLING_AS = re.compile(r"ENROLLING FINGER AS ID #(\d+)", re.IGNORECASE)
RE_ENROLL_SUCCESS = re.compile(r"SUCCESS!?\s*Finger saved as ID #(\d+)", re.IGNORECASE)
RE_ENROLL_CANCEL = re.compile(r"ENROLLMENT cancelled|Enrollment cancelled|ENROLL_CANCELLED", re.IGNORECASE)
RE_WIPE_START = re.compile(r"Wiping ALL fingerprints", re.IGNORECASE)
RE_WIPE_SUCCESS = re.compile(r"SUCCESS\s*-\s*All fingerprints deleted", re.IGNORECASE)
RE_DELETE_START = re.compile(r"Deleting ID #(\d+)", re.IGNORECASE)
RE_DELETE_SUCCESS = re.compile(r"SUCCESS\s*-\s*ID #(\d+) deleted", re.IGNORECASE)
RE_DELETE_FAIL = re.compile(r"FAILED\s*-\s*Could not delete ID #(\d+)", re.IGNORECASE)
RE_STORED_COUNT = re.compile(r"Stored fingerprints:\s*(\d+)", re.IGNORECASE)


_FORMULA_TRIGGER_CHARS = ("=", "+", "-", "@", "\t", "\r")


def _sanitize_csv_cell(value: Any) -> str:
    """Neutralize CSV/formula-injection payloads (CWE-1236) before writing.

    Ported verbatim from archive/legacy-ui/v2/python/gui_qt/pages/reports_page.py.
    student_no / student_name / grade / section are free-text fields with no
    restriction on leading characters. If a value starts with '=', '+', '-',
    or '@', Excel and similar tools interpret the cell as a formula when the
    exported file is opened. v3's export functions built their own CSV
    writing and never had this check, reintroducing the exact vulnerability
    v2 explicitly patched.
    """
    text = "" if value is None else str(value)
    if text.startswith(_FORMULA_TRIGGER_CHARS):
        return "'" + text
    return text


def _student_label(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not row:
        return {}
    return {
        "fingerprint_id": row.get("fingerprint_id"),
        "student_no": row.get("student_no"),
        "student_name": row.get("student_name"),
        "grade": row.get("grade"),
        "section": row.get("section"),
    }


class _UILogHandler(logging.Handler):
    """Mirrors every log record emitted this run into the web UI live.

    v2 (Qt) did this by having core.logger call straight into a Qt widget's
    append_record() as each line was logged - a live push, not a periodic
    re-read of the log file. v3's original get_app_log() instead read a
    fixed filename that core/logger.py no longer writes to (it creates one
    timestamped file per run), so the Logs page only ever showed whatever
    old file happened to still have that name. This handler restores the
    same push-based behavior, formatted identically to the file/console
    output, and also backs the in-memory buffer get_app_log() serves from -
    so the page works correctly even if file logging is disabled entirely.
    """

    def __init__(self, api: "Api", max_lines: int = 2000) -> None:
        super().__init__()
        self._api = api
        self._max_lines = max_lines
        self.setFormatter(
            AppFormatter("%(asctime)s | %(levelname)-7s | %(source)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S.%f")
        )

    def emit(self, record: logging.LogRecord) -> None:
        try:
            line = self.format(record)
        except Exception:
            return
        with self._api._app_log_lock:
            self._api._app_log_lines.append(line)
            if len(self._api._app_log_lines) > self._max_lines:
                del self._api._app_log_lines[: len(self._api._app_log_lines) - self._max_lines]
        self._api._push("log_line", {"line": line})


class Api:
    """Exposed to the web page as ``window.pywebview.api``."""

    def __init__(self) -> None:
        self._window = None  # set by main_web.py after window creation
        self._app_log_lines: List[str] = []
        self._app_log_lock = threading.Lock()

        # Attached before anything else so this run's own startup log lines
        # (SerialHandler init, database ready, etc.) are captured too - not
        # just log lines emitted after the UI happens to visit the page.
        self._log_handler = _UILogHandler(self)
        LOG.addHandler(self._log_handler)

        self.serial = SerialHandler()
        self.processor = AttendanceProcessor()
        self._read_thread: Optional[threading.Thread] = None
        self._read_stop = threading.Event()
        self._observed_connected = False
        self._scanning = False  # whether we've told the device to enter SCAN_MODE
        self._device_mode = "command"  # "scan" | "command", as reported by the device itself
        self._pending_delete_id: Optional[int] = None
        self._pending_enroll = False
        self._pending_wipe = False

        try:
            db.init_database()
        except Exception as exc:  # pragma: no cover - defensive
            log.error(f"Database initialization failed: {exc}")

        # Apply persisted connection preferences to the handler itself -
        # v3 previously loaded auto_reconnect/auto_detect_serial into the
        # Settings page but never actually applied them to SerialHandler,
        # so the toggles were cosmetic. Mirrors MainWindow.__init__ in v2.
        settings = load_settings()
        self.serial.auto_reconnect_enabled = bool(settings.get("auto_reconnect", True))
        try:
            self.processor.cooldown_seconds = max(1, int(settings.get("cooldown", self.processor.cooldown_seconds)))
            self.processor.min_confidence = max(1, min(100, int(settings.get("min_confidence", self.processor.min_confidence))))
        except (TypeError, ValueError):
            log.warning("Invalid persisted attendance settings; using processor defaults")

        # Recurring auto-backup, ported from MainWindow._configure_auto_backup_timer
        # / _run_auto_backup_check - v3 had the "Auto-backup interval" field
        # in Settings but nothing was ever actually scheduling backups with
        # it. Runs an initial check shortly after startup, then on a
        # recurring interval matching the configured minutes.
        self._backup_stop = threading.Event()
        self._backup_interval_minutes = float(settings.get("auto_backup_interval_minutes", 25))
        self._backup_thread = threading.Thread(target=self._auto_backup_loop, daemon=True)
        self._backup_thread.start()

    def _auto_backup_loop(self) -> None:
        """Checks every ~12s (interval / 5, same ratio v2 used) whether a
        backup is due, so a settings change to the interval takes effect
        quickly instead of waiting up to the old interval's length."""
        time.sleep(2)  # let startup settle first, like v2's singleShot(2000, ...)
        while not self._backup_stop.is_set():
            try:
                path = db.auto_backup_if_needed(min_interval_hours=self._backup_interval_minutes / 60.0)
                if path:
                    log.info(f"Automatic backup created: {path}")
            except Exception as exc:
                log.error(f"Auto-backup check failed: {exc}")
            self._backup_stop.wait(max(5.0, (self._backup_interval_minutes * 60) / 5))
    def set_window(self, window) -> None:
        self._window = window

    def _push(self, event: str, payload: Any) -> None:
        """Fire a JS-side event so the UI updates without polling.

        Calls a `window.dsisEvent(event, payload)` function that app.js
        defines; failures here (e.g. window not ready yet) are swallowed
        so a UI hiccup never takes down the backend thread.
        """
        if self._window is None:
            return
        try:
            import json

            self._window.evaluate_js(
                f"window.dsisEvent && window.dsisEvent({json.dumps(event)}, {json.dumps(payload, default=str)})"
            )
        except Exception:
            pass

    # -- connection ---------------------------------------------------------------
    def list_ports(self) -> List[str]:
        return list_serial_ports()

    def list_ports_detailed(self) -> List[Dict[str, str]]:
        """Same idea as v2's port dropdown: VID:PID + device + description."""
        try:
            from serial.tools import list_ports as _list_ports
        except Exception:
            return [{"device": p, "label": p} for p in list_serial_ports()]
        results = []
        try:
            for port_info in _list_ports.comports():
                device = getattr(port_info, "device", None)
                if not device:
                    continue
                vid = getattr(port_info, "vid", None)
                pid = getattr(port_info, "pid", None)
                vid_pid = f"{vid:04x}:{pid:04x}" if vid is not None and pid is not None else "UNKNOWN"
                description = (getattr(port_info, "description", "") or "").strip()
                label = f"{vid_pid} \u2014 {device}" + (f" ({description})" if description else "")
                results.append({"device": device, "label": label})
        except Exception:
            pass
        return results

    def forget_saved_port(self) -> Dict[str, Any]:
        settings = load_settings()
        settings["com_port"] = ""
        save_settings(settings)
        return {"ok": True}

    def connect(self, port: str = "", baud: int = 0, auto_detect: Optional[bool] = None) -> Dict[str, Any]:
        baud = baud or CONFIG.baud_rate
        if auto_detect is None:
            auto_detect = bool(load_settings().get("auto_detect_serial", True))
        ok, message = self.serial.connect(port=port or "", baud=baud, auto_detect=bool(auto_detect))
        if ok:
            settings = load_settings()
            settings["com_port"] = self.serial.reconnect_port or port
            settings["baud_rate"] = baud
            save_settings(settings)
            self._start_read_loop()
            self._push("connection_status", self.get_connection_status())
            self.request_fingerprint_count()
        return {
            "connected": ok,
            "message": message,
            "port": self.serial.reconnect_port,
            "baud": self.serial.reconnect_baud,
            "device_metadata": self.serial.device_metadata,
        }

    def disconnect(self) -> Dict[str, Any]:
        try:
            if self.serial.is_connected():
                cmds.cmd_stop(self.serial)
        except Exception:
            pass
        self._stop_read_loop()
        self._observed_connected = False
        self._scanning = False
        self._device_mode = "command"
        self._pending_enroll = False
        self._pending_delete_id = None
        self._pending_wipe = False
        self.serial.disconnect()
        self._push("connection_status", self.get_connection_status())
        return {"connected": False}

    def get_connection_status(self) -> Dict[str, Any]:
        return {
            "connected": self.serial.is_connected(),
            "port": self.serial.reconnect_port,
            "baud": self.serial.reconnect_baud,
            "device_metadata": self.serial.device_metadata,
            "scanning": self._scanning,
            "device_mode": self._device_mode,
        }

    # -- scanning -------------------------------------------------------------
    def _operation_conflict(self, operation: str) -> Optional[str]:
        if self._pending_enroll:
            return "Enrollment is already in progress."
        if self._pending_delete_id is not None:
            return "Fingerprint deletion is already in progress."
        if self._pending_wipe:
            return "Fingerprint wipe is already in progress."
        if operation != "scan" and self._scanning:
            return "Stop attendance scanning before starting this operation."
        return None

    def start_scan(self) -> bool:
        if not permissions.require_permission("scan"):
            return False
        if not self.serial.is_connected():
            return False
        if self._operation_conflict("scan"):
            return False
        ok = cmds.cmd_scan(self.serial)
        if ok:
            self._scanning = True
            self._device_mode = "scan"
            self._push("mode_changed", {"mode": "scan"})
        return ok

    def stop_scan(self) -> bool:
        if not permissions.require_permission("scan"):
            return False
        ok = cmds.cmd_stop(self.serial) if self.serial.is_connected() else True
        self._scanning = False
        self._device_mode = "command"
        self._push("mode_changed", {"mode": "command"})
        return ok

    # -- enrollment (real hardware flow, ported from v2's EnrollDialog) -----------
    def start_enroll(self) -> Dict[str, Any]:
        """Tell the device to begin enrolling the next finger it sees.

        The firmware auto-assigns the fingerprint ID - it is NOT chosen by
        the caller. Mirrors v2: send STOP (cancel any active scan) then
        ENROLL, then wait for the enroll_progress push events
        ("enrolling" -> "success"/"cancelled"/"error") that the read loop
        parses from the device's own output. Only after a "success" event
        (which carries the assigned id) should the caller persist a student
        record via save_student().
        """
        if not self.serial.is_connected():
            return {"ok": False, "message": "Connect to the ESP32 first."}
        if not permissions.require_permission("enroll"):
            return {"ok": False, "message": "Current role does not have enroll permission."}
        conflict = self._operation_conflict("enroll")
        if conflict:
            return {"ok": False, "message": conflict}
        cmds.cmd_stop(self.serial)
        self._scanning = False
        self._device_mode = "command"
        self._push("mode_changed", {"mode": "command"})
        self._pending_enroll = True
        ok = cmds.cmd_enroll(self.serial)
        if not ok:
            self._pending_enroll = False
            return {"ok": False, "message": "Could not send ENROLL command to the ESP32."}
        return {"ok": True, "message": "Sent ENROLL command. Follow the prompts on the sensor."}

    def cancel_enroll(self) -> Dict[str, Any]:
        """Cancel an active enrollment before the modal is closed."""
        if not self._pending_enroll:
            return {"ok": True, "message": "No enrollment is active."}
        if not self.serial.is_connected():
            self._pending_enroll = False
            return {"ok": False, "message": "The ESP32 is disconnected; enrollment state was cleared locally."}
        ok = cmds.cmd_stop(self.serial)
        self._pending_enroll = False
        return {"ok": ok, "message": "Enrollment cancelled." if ok else "Could not cancel enrollment on the ESP32."}

    # -- deletion (real hardware flow, ported from v2's DeleteDialog) -------------
    def delete_on_device(self, fingerprint_id: int) -> Dict[str, Any]:
        """Send DELETE:<id> to the device and wait for its own confirmation.

        Deliberately does NOT touch the local database - the frontend should
        wait for a 'delete_progress' push event with status "success" for
        this same id, and only then call delete_student() to remove the
        local row. This is the exact bug v2's DeleteDialog docstring
        describes fixing: firing DELETE and deleting locally unconditionally
        let the DB and the sensor drift out of sync.
        """
        if not self.serial.is_connected():
            return {"ok": False, "message": "Connect to the ESP32 first \u2014 deleting while disconnected is disabled so the database and the sensor can't drift out of sync."}
        if not permissions.require_permission("delete"):
            return {"ok": False, "message": "Current role does not have delete permission."}
        conflict = self._operation_conflict("delete")
        if conflict:
            return {"ok": False, "message": conflict}
        self._pending_delete_id = int(fingerprint_id)
        ok = cmds.cmd_delete(self.serial, int(fingerprint_id))
        if not ok:
            self._pending_delete_id = None
            return {"ok": False, "message": "Could not send DELETE command to the ESP32."}
        return {"ok": True, "message": f"Deleting fingerprint ID {fingerprint_id} on the device\u2026"}

    def wipe_all_on_device(self) -> Dict[str, Any]:
        if not self.serial.is_connected():
            return {"ok": False, "message": "Connect to the ESP32 first."}
        if not permissions.require_permission("wipe"):
            return {"ok": False, "message": "Current role does not have wipe permission."}
        conflict = self._operation_conflict("wipe")
        if conflict:
            return {"ok": False, "message": conflict}
        self._pending_wipe = True
        ok = cmds.cmd_wipe(self.serial)
        if not ok:
            self._pending_wipe = False
        return {"ok": ok, "message": "Wiping ALL fingerprints\u2026" if ok else "Could not send WIPE command."}

    def request_fingerprint_count(self) -> bool:
        if not self.serial.is_connected():
            return False
        if not permissions.require_permission("scan"):
            return False
        return cmds.cmd_list(self.serial)

    # -- the always-on read loop --------------------------------------------------
    def _start_read_loop(self) -> None:
        """Starts reading serial output the moment we're connected - not
        gated behind the SCAN toggle. v3 previously only read the port while
        _scanning was true, which meant Enroll/Delete/Wipe/List responses
        (and anything else the device prints outside of active scanning)
        were silently dropped on the floor, because nothing was calling
        read_line() to receive them. This mirrors v2's SerialWorker, which
        runs continuously for the whole time the device is connected.
        """
        if self._read_thread and self._read_thread.is_alive():
            return
        self._read_stop.clear()
        self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._read_thread.start()

    def _stop_read_loop(self) -> None:
        self._read_stop.set()
        thread = self._read_thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=1.0)
        if thread and not thread.is_alive():
            self._read_thread = None

    def _sync_connection_state(self) -> bool:
        """Publish serial transitions and invalidate device operations on loss."""
        connected = self.serial.is_connected()
        if connected == self._observed_connected:
            return connected

        self._observed_connected = connected
        if not connected:
            self._scanning = False
            self._device_mode = "command"
            self._pending_enroll = False
            self._pending_delete_id = None
            self._pending_wipe = False
        self._push("connection_status", self.get_connection_status())
        self._push("connection_changed", {"connected": connected})
        return connected

    def _read_loop(self) -> None:
        while not self._read_stop.is_set():
            connected = self._sync_connection_state()
            if not connected:
                time.sleep(0.5)
                continue
            try:
                line = self.serial.read_line()
            except Exception as exc:
                log.error(f"Serial read error: {exc}")
                self._push("serial_error", {"message": str(exc)})
                self.serial.connected = False
                self._sync_connection_state()
                time.sleep(0.2)
                continue
            if not line:
                time.sleep(0.05)
                continue

            self._append_serial_log(line, "rx")
            if self.serial.should_ignore(line):
                continue

            # Every incoming line gets run through all parsers, exactly like
            # v2's SerialWorker.run() - these are independent, not mutually
            # exclusive checks (a single line is normally only ever matched
            # by one of them, but nothing stops it from being checked by all).
            self._parse_mode_line(line)
            self._parse_scan_line(line)
            self._parse_enroll_progress(line)
            self._parse_wipe_progress(line)
            self._parse_delete_progress(line)
            self._parse_fingerprint_count(line)

    def _parse_mode_line(self, line: str) -> None:
        parsed = parse_json_line(line)
        state = None
        if parsed is not None and parsed.get("type") == "status":
            state = parsed.get("state")
        elif line in ("SCAN_MODE", "CMD_MODE"):
            state = line
        if state == "SCAN_MODE":
            self._device_mode = "scan"
            self._push("mode_changed", {"mode": "scan"})
        elif state == "CMD_MODE":
            self._device_mode = "command"
            self._push("mode_changed", {"mode": "command"})

    def _parse_scan_line(self, line: str) -> None:
        result = self.processor.process_line(line)
        if result is None:
            return
        student = self.processor.lookup_student(result["fingerprint_id"]) if result.get("fingerprint_id") else None
        payload = {
            "fingerprint_id": result.get("fingerprint_id"),
            "confidence": result.get("confidence"),
            "status": result.get("status"),
            "logged": result.get("logged"),
            "reason": result.get("reason"),
            "timestamp": result.get("timestamp").isoformat() if result.get("timestamp") else None,
            "student": _student_label(student),
        }
        self._push("scan_result", payload)

    def _parse_enroll_progress(self, message: str) -> None:
        message = message.strip()
        if not message:
            return
        match = RE_ENROLLING_AS.search(message)
        if match:
            self._push("enroll_progress", {"event": "enrolling", "id": match.group(1)})
            return
        match = RE_ENROLL_SUCCESS.search(message)
        if match:
            self._pending_enroll = False
            self._push("enroll_progress", {"event": "success", "id": match.group(1)})
            return
        if RE_ENROLL_CANCEL.search(message):
            self._pending_enroll = False
            self._push("enroll_progress", {"event": "cancelled", "id": None})
            return
        if self._pending_enroll:
            upper = message.upper()
            if "ERROR" in upper or "FAIL" in upper:
                self._pending_enroll = False
                self._push("enroll_progress", {"event": "error", "id": None})

    def _parse_wipe_progress(self, message: str) -> None:
        if RE_WIPE_START.search(message):
            self._pending_wipe = True
            self._push("wipe_progress", {"event": "start"})
            return
        if RE_WIPE_SUCCESS.search(message):
            self._pending_wipe = False
            self._push("wipe_progress", {"event": "success"})
            self.request_fingerprint_count()
            return
        if self._pending_wipe:
            upper = message.upper()
            if "ERROR" in upper or "FAIL" in upper or "CANCEL" in upper:
                self._pending_wipe = False
                self._push("wipe_progress", {"event": "error", "message": message})

    def _parse_delete_progress(self, message: str) -> None:
        match = RE_DELETE_START.search(message)
        if match:
            self._push("delete_progress", {"event": "start", "id": int(match.group(1))})
            return
        match = RE_DELETE_SUCCESS.search(message)
        if match:
            self._pending_delete_id = None
            self._push("delete_progress", {"event": "success", "id": int(match.group(1))})
            return
        match = RE_DELETE_FAIL.search(message)
        if match:
            self._pending_delete_id = None
            self._push("delete_progress", {"event": "error", "id": int(match.group(1))})

    def _parse_fingerprint_count(self, line: str) -> None:
        match = RE_STORED_COUNT.search(line)
        if match:
            self._push("fingerprint_count", {"count": int(match.group(1))})

    def send_serial_command(self, cmd: str) -> bool:
        if not cmd or not self.serial.is_connected():
            return False
        if permissions.get_current_role() != "admin":
            return False
        command = cmd.strip().upper()
        if command not in {"LIST", "HELP", "STOP", "SCAN", "ID?", "RESET"}:
            return False
        self._append_serial_log(f"> {cmd}", "tx")
        return self.serial.send_command(cmd)

    def reset_device(self) -> bool:
        if not self.serial.is_connected():
            return False
        if permissions.get_current_role() != "admin":
            return False
        return self.serial.reset_device()

    def _append_serial_log(self, text: str, direction: str) -> None:
        self._push("serial_line", {"text": text, "direction": direction})

    # -- dashboard / attendance -------------------------------------------------
    def get_dashboard_stats(self) -> Dict[str, Any]:
        info = db.get_today_attendance_info()
        rows = info["rows"]
        scans_today = len(rows)
        total_students = db.get_student_count()
        unknown_scans = sum(1 for r in rows if not r.get("student_no") or r.get("student_no") == "N/A")
        present_students = len(
            {r.get("student_no") for r in rows if r.get("student_no") and r.get("student_no") != "N/A"}
        )
        rate = round((present_students / total_students) * 100) if total_students else 0
        last_scan = rows[0] if rows else None
        return {
            "scans_today": scans_today,
            "total_students": total_students,
            "attendance_rate": rate,
            "present_count": present_students,
            "unknown_scans": unknown_scans,
            "is_fallback": info.get("is_fallback", False),
            "last_scan_time": last_scan.get("time") if last_scan else None,
        }

    def get_recent_activity(self, limit: int = 25) -> List[Dict[str, Any]]:
        return db.get_attendance_paginated(limit=limit, offset=0)

    def get_attendance(self, mode: str = "today", offset: int = 0) -> Dict[str, Any]:
        mode = (mode or "today").lower()
        page_size = 100
        if mode == "today":
            rows = db.get_attendance_today()
            has_more = False
        elif mode == "last30" or mode == "last 30 days":
            start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            end = datetime.now().strftime("%Y-%m-%d")
            rows = list(reversed(db.export_attendance_range(start, end)))
            has_more = False
        else:  # recent - paginated, matching v2's AttendancePage Prev/Next
            rows = db.get_attendance_paginated(limit=page_size, offset=offset)
            has_more = len(rows) == page_size
        return {"rows": rows, "offset": offset, "has_more": has_more}

    def export_attendance_csv(self, mode: str = "today") -> Dict[str, Any]:
        if not permissions.require_permission("export"):
            return {"ok": False, "message": "Current role does not have export permission."}
        rows = self.get_attendance(mode)["rows"]
        return self._rows_to_csv(rows, f"attendance_{mode}")

    # -- students ---------------------------------------------------------------
    def get_students(self) -> List[Dict[str, Any]]:
        return db.get_all_students()

    def get_student(self, fingerprint_id: int) -> Dict[str, Any]:
        return db.get_student(fingerprint_id) or {}

    def save_student(
        self,
        fingerprint_id: int,
        student_no: str,
        student_name: str,
        grade: str,
        section: str,
    ) -> Dict[str, Any]:
        if not permissions.require_permission("enroll"):
            return {"ok": False, "message": "Current role does not have enroll permission."}
        ok, message = db.register_student(int(fingerprint_id), student_no, student_name, grade, section)
        return {"ok": ok, "message": message}

    def delete_student(self, fingerprint_id: int) -> Dict[str, Any]:
        if not permissions.require_permission("delete"):
            return {"ok": False, "message": "Current role does not have delete permission."}
        try:
            db.delete_student(int(fingerprint_id))
            return {"ok": True, "message": "Deleted"}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}

    def export_students_csv(self) -> Dict[str, Any]:
        if not permissions.require_permission("export"):
            return {"ok": False, "message": "Current role does not have export permission."}
        rows = self.get_students()
        return self._rows_to_csv(rows, "students")

    def _rows_to_csv(self, rows: List[Dict[str, Any]], name_prefix: str) -> Dict[str, Any]:
        if not rows:
            return {"ok": False, "message": "No data to export."}
        export_dir = Path(CONFIG.export_folder)
        export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = export_dir / f"{name_prefix}_{timestamp}.csv"
        with out_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow({key: _sanitize_csv_cell(value) for key, value in row.items()})
        return {"ok": True, "message": f"Exported {len(rows)} rows", "path": str(out_path)}

    # -- reports / backups --------------------------------------------------------
    def get_statistics_report(self) -> Dict[str, Any]:
        if not (permissions.has_permission("export") or permissions.has_permission("backup")):
            return {"ok": False, "message": "Current role does not have report permission."}
        summary = db.get_daily_attendance_summary()
        totals: Dict[str, Dict[str, Any]] = {}
        for row in summary:
            key = row["student_name"]
            entry = totals.setdefault(
                key,
                {
                    "student_name": row["student_name"],
                    "student_no": row.get("student_no"),
                    "grade": row.get("grade"),
                    "section": row.get("section"),
                    "count": 0,
                },
            )
            entry["count"] += 1
        students = sorted(totals.values(), key=lambda x: x["count"], reverse=True)
        total_records = sum(s["count"] for s in students)
        by_grade: Dict[str, int] = {}
        for s in students:
            by_grade[s["grade"] or "Unknown"] = by_grade.get(s["grade"] or "Unknown", 0) + 1
        return {
            "total_students": db.get_student_count(),
            "total_records": total_records,
            "avg_per_student": round(total_records / len(students), 1) if students else 0,
            "top_students": students[:10],
            "by_grade": by_grade,
            "all_students": students,
        }

    def list_backups(self) -> List[Dict[str, Any]]:
        if not permissions.require_permission("backup"):
            return []
        return db.list_backups()

    def create_backup(self) -> Dict[str, Any]:
        if not permissions.require_permission("backup"):
            return {"ok": False, "message": "Current role does not have backup permission."}
        ok, message, path = db.backup_database()
        return {"ok": ok, "message": message, "path": path}

    def restore_backup(self, backup_path: str) -> Dict[str, Any]:
        if not permissions.require_permission("restore"):
            return {"ok": False, "message": "Current role does not have restore permission."}
        ok, message = db.restore_database(backup_path)
        if ok:
            self._push("data_changed", {"reason": "restore"})
        return {"ok": ok, "message": message}

    # -- settings -----------------------------------------------------------------
    def get_settings(self) -> Dict[str, Any]:
        settings = load_settings()
        settings["available_ports"] = list_serial_ports()
        settings["log_folder"] = str(CONFIG.log_folder)
        backups = db.list_backups()
        settings["last_backup"] = backups[0]["name"] if backups else None
        return settings

    def save_ui_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        if permissions.get_current_role() != "admin":
            return {"ok": False, "message": "Current role does not have settings permission."}
        merged = load_settings()
        try:
            cooldown = max(1, min(60, int(settings.get("cooldown", merged.get("cooldown", 10)))))
            confidence = max(1, min(100, int(settings.get("min_confidence", merged.get("min_confidence", 96)))))
            backup_interval = max(1, min(180, int(settings.get("auto_backup_interval_minutes", merged.get("auto_backup_interval_minutes", 25)))))
        except (TypeError, ValueError):
            return {"ok": False, "message": "Attendance and backup settings must be valid numbers."}
        settings = dict(settings)
        settings.update({"cooldown": cooldown, "min_confidence": confidence, "auto_backup_interval_minutes": backup_interval})
        merged.update({k: v for k, v in settings.items() if k in merged})
        save_settings(merged)

        # Apply the parts of settings that aren't just persisted-for-next-time
        # but should take effect immediately, mirroring MainWindow.apply_settings.
        if "auto_reconnect" in settings:
            self.serial.auto_reconnect_enabled = bool(settings["auto_reconnect"])
        if "auto_backup_interval_minutes" in settings:
            self._backup_interval_minutes = float(backup_interval)
        self.processor.cooldown_seconds = cooldown
        self.processor.min_confidence = confidence

        return {"ok": True}

    def get_current_role(self) -> str:
        return permissions.get_current_role()

    def set_current_role(self, role: str) -> Dict[str, Any]:
        if role not in CONFIG.user_roles:
            return {"ok": False, "message": "Unknown role."}
        settings = load_settings()
        settings["current_role"] = role
        save_settings(settings)
        return {"ok": True, "permissions": CONFIG.user_roles.get(role, {}).get("permissions", [])}

    def get_role_permissions(self, role: str) -> List[str]:
        return CONFIG.user_roles.get(role, {}).get("permissions", [])

    def open_log_folder(self) -> Dict[str, Any]:
        folder = str(CONFIG.log_folder)
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}

    # -- application log ------------------------------------------------------------
    def get_app_log(self, max_lines: int = 500) -> List[str]:
        with self._app_log_lock:
            if self._app_log_lines:
                return list(self._app_log_lines[-max_lines:])
        # Fallback: buffer is empty for some reason (e.g. handler failed to
        # attach) - read straight from this run's actual timestamped log
        # file (core.logger.LOG_FILE), not a fixed filename, since
        # core/logger.py creates a fresh file per run rather than a single
        # persistent one.
        if not LOG_FILE or not Path(LOG_FILE).exists():
            return []
        try:
            with Path(LOG_FILE).open("r", encoding="utf-8", errors="ignore") as handle:
                lines = handle.readlines()
            return [line.rstrip("\n") for line in lines[-max_lines:]]
        except Exception as exc:
            log.error(f"Failed to read app log: {exc}")
            return []
