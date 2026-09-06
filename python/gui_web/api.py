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
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_config
from core import database as db
from core import permissions
from core.attendance import AttendanceProcessor
from core.logger import log
from core.serial_handler import SerialHandler, list_serial_ports
from settings_store import load_settings, save_settings

CONFIG = get_config()


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


class Api:
    """Exposed to the web page as ``window.pywebview.api``."""

    def __init__(self) -> None:
        self._window = None  # set by main_web.py after window creation
        self.serial = SerialHandler()
        self.processor = AttendanceProcessor()
        self._scan_thread: Optional[threading.Thread] = None
        self._scan_stop = threading.Event()
        self._scanning = False
        self._app_log_lines: List[str] = []
        self._app_log_lock = threading.Lock()

        try:
            db.init_database()
        except Exception as exc:  # pragma: no cover - defensive
            log.error(f"Database initialization failed: {exc}")

    # -- wiring from main_web.py -------------------------------------------------
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

    def connect(self, port: str = "", baud: int = 0, auto_detect: bool = False) -> Dict[str, Any]:
        baud = baud or CONFIG.baud_rate
        ok, message = self.serial.connect(port=port or "", baud=baud, auto_detect=auto_detect or not port)
        if ok:
            settings = load_settings()
            settings["com_port"] = self.serial.reconnect_port or port
            settings["baud_rate"] = baud
            save_settings(settings)
        return {
            "connected": ok,
            "message": message,
            "port": self.serial.reconnect_port,
            "baud": self.serial.reconnect_baud,
            "device_metadata": self.serial.device_metadata,
        }

    def disconnect(self) -> Dict[str, Any]:
        self._stop_scan_loop()
        self.serial.disconnect()
        return {"connected": False}

    def get_connection_status(self) -> Dict[str, Any]:
        return {
            "connected": self.serial.is_connected(),
            "port": self.serial.reconnect_port,
            "baud": self.serial.reconnect_baud,
            "device_metadata": self.serial.device_metadata,
            "scanning": self._scanning,
        }

    # -- scanning -------------------------------------------------------------
    def start_scan(self) -> bool:
        if not self.serial.is_connected():
            return False
        ok = self.serial.send_command("SCAN")
        if ok:
            self._scanning = True
            self._start_scan_loop()
        return ok

    def stop_scan(self) -> bool:
        ok = self.serial.send_command("STOP") if self.serial.is_connected() else True
        self._scanning = False
        self._stop_scan_loop()
        return ok

    def _start_scan_loop(self) -> None:
        if self._scan_thread and self._scan_thread.is_alive():
            return
        self._scan_stop.clear()
        self._scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._scan_thread.start()

    def _stop_scan_loop(self) -> None:
        self._scan_stop.set()

    def _scan_loop(self) -> None:
        while not self._scan_stop.is_set():
            if not self.serial.is_connected():
                time.sleep(0.5)
                continue
            line = self.serial.read_line()
            if line is None:
                time.sleep(0.05)
                continue
            self._append_serial_log(line, "rx")
            if self.serial.should_ignore(line):
                continue
            result = self.processor.process_line(line)
            if result is None:
                continue
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

    def send_serial_command(self, cmd: str) -> bool:
        if not cmd or not self.serial.is_connected():
            return False
        self._append_serial_log(f"> {cmd}", "tx")
        return self.serial.send_command(cmd)

    def reset_device(self) -> bool:
        if not self.serial.is_connected():
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

    def get_attendance(self, mode: str = "today") -> List[Dict[str, Any]]:
        mode = (mode or "today").lower()
        if mode == "today":
            return db.get_attendance_today()
        if mode == "last30" or mode == "last 30 days":
            start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            return db.get_daily_attendance_summary(start_date=start)
        return db.get_attendance_paginated(limit=200, offset=0)

    def export_attendance_csv(self, mode: str = "today") -> Dict[str, Any]:
        rows = self.get_attendance(mode)
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
            writer.writerows(rows)
        return {"ok": True, "message": f"Exported {len(rows)} rows", "path": str(out_path)}

    # -- reports / backups --------------------------------------------------------
    def get_statistics_report(self) -> Dict[str, Any]:
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
        return db.list_backups()

    def create_backup(self) -> Dict[str, Any]:
        ok, message, path = db.backup_database()
        return {"ok": ok, "message": message, "path": path}

    def restore_backup(self, backup_path: str) -> Dict[str, Any]:
        if not permissions.require_permission("restore"):
            return {"ok": False, "message": "Current role does not have restore permission."}
        ok, message = db.restore_database(backup_path)
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
        merged = load_settings()
        merged.update({k: v for k, v in settings.items() if k in merged})
        save_settings(merged)
        return {"ok": True}

    def get_current_role(self) -> str:
        return permissions.get_current_role()

    def set_current_role(self, role: str) -> Dict[str, Any]:
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
        log_file = CONFIG.log_folder / CONFIG.log_file_name
        if not log_file.exists():
            return []
        try:
            with log_file.open("r", encoding="utf-8", errors="ignore") as handle:
                lines = handle.readlines()
            return [line.rstrip("\n") for line in lines[-max_lines:]]
        except Exception as exc:
            log.error(f"Failed to read app log: {exc}")
            return []
