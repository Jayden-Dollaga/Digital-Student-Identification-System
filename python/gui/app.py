"""Main application shell for the fingerprint attendance desktop UI.

The GUI remains responsible for user interaction and orchestration, while the
core modules handle serial communication, attendance interpretation, and data
persistence.
"""

import sys
import threading
import time
import re
from pathlib import Path
from datetime import datetime
from tkinter import messagebox

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

import customtkinter as ctk

from config import get_config
from gui.layout_utils import resolve_window_size

CONFIG = get_config()
from core.serial_handler import SerialHandler
from core.attendance import AttendanceProcessor
from core.database import get_student, log_attendance
from settings_store import default_settings, load_settings, save_settings
from core.commands import cmd_scan, cmd_stop, cmd_enroll, cmd_wipe, cmd_list
from gui.sidebar import build_sidebar
from gui.attendance_page import AttendancePage, build_attendance_card
from gui.statistics_page import build_statistics_tab
from gui.log_page import build_log_tab
from gui.settings_dialog import open_settings_dialog
from gui.dialogs import open_enroll_dialog, save_enroll_profile, close_enroll_dialog, open_wipe_dialog, confirm_wipe, close_wipe_dialog, open_restore_dialog
from gui import reports_page
from gui.students_page import (
    StudentsPage,
    open_students_list_dialog,
)
from gui.dashboard import DashboardPage
from gui.settings_page import SettingsPage
from gui.theme import apply_default_theme, apply_appearance_mode
from gui.perf_profiler import PerfProfiler
from gui.serial_troubleshooting import build_serial_troubleshooting_message, build_common_port_candidates, open_device_manager, open_driver_help
from core.database import (
    init_database,
    clear_all_data,
    backup_database as backup_database_service,
)
from core.utils import format_attendance_display, parse_json_line

# ---- Palette -----------------------------------------------------------
COLOR_CONNECTED = "#2ecc71"
COLOR_DISCONNECTED = "#e74c3c"
COLOR_MUTED = "#8b8b8b"
COLOR_ACCENT = "#3b82f6"
COLOR_DANGER = "#e74c3c"
COLOR_DANGER_HOVER = "#c0392b"
MONO_FONT = ("Consolas", 12)
HEADER_FONT = ("Segoe UI", 16, "bold")
SUBHEADER_FONT = ("Segoe UI", 13, "bold")

# ESP32 output patterns that drive the enroll popup
RE_ENROLLING_AS = re.compile(r"ENROLLING FINGER AS ID #(\d+)", re.IGNORECASE)
RE_ENROLL_SUCCESS = re.compile(r"SUCCESS!?\s*Finger saved as ID #(\d+)", re.IGNORECASE)
RE_ENROLL_CANCEL = re.compile(r"ENROLLMENT cancelled|Enrollment cancelled|ENROLL_CANCELLED", re.IGNORECASE)

# ESP32 output patterns that drive the wipe popup
RE_WIPE_START = re.compile(r"Wiping ALL fingerprints", re.IGNORECASE)
RE_WIPE_SUCCESS = re.compile(r"SUCCESS\s*-\s*All fingerprints deleted", re.IGNORECASE)

# ESP32 output patterns for attendance logging
RE_SCAN_MODE = re.compile(r"SCAN_MODE", re.IGNORECASE)
RE_CMD_MODE = re.compile(r"CMD_MODE", re.IGNORECASE)


class FingerprintApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Fingerprint Attendance System")
        # Load settings early so we can respect the user's choice about automatic scaling
        self.settings = load_settings()

        self._screen_width = self.winfo_screenwidth() if self.winfo_screenwidth() > 0 else 1440
        self._screen_height = self.winfo_screenheight() if self.winfo_screenheight() > 0 else 900
        window_width, window_height = resolve_window_size(self._screen_width, self._screen_height)
        self.geometry(f"{window_width}x{window_height}")
        # Allow smaller screens to run the app; reduce hard minimums
        self.minsize(720, 480)

        # Compute a responsive scaling factor based on available screen width
        base_width = 1440
        try:
            self.scaling_factor = max(0.7, min(1.2, self._screen_width / base_width))
        except Exception:
            self.scaling_factor = 1.0
        ctk.set_default_color_theme("blue")

        self.serial_handler = SerialHandler()
        self.attendance_processor = AttendanceProcessor()
        self.stop_event = threading.Event()
        self.reader_thread = None
        self.scan_mode_active = False
        self.enroll_mode_active = False
        self.wipe_mode_active = False
        self._closing = False
        self.protocol("WM_DELETE_WINDOW", self.quit_app)

        # Enroll popup state
        self.enroll_dialog = None
        self.enroll_log_text = None
        self.enroll_save_button = None
        self.enroll_completed = False
        self.enroll_ready_to_save = False

        # Wipe popup state
        self.wipe_dialog = None
        self.wipe_log_text = None
        self.wipe_status_var = None
        self.wipe_confirm_button = None

        # Student roster popup state (opened from "List")
        self.students_dialog = None
        self.students_list_frame = None

        # User role system
        self.current_role = CONFIG.default_user_role

        self.dashboard_page = DashboardPage(self)
        self.students_page = StudentsPage(self)
        self.attendance_page = AttendancePage(self)
        self.settings_page = SettingsPage(self)

        self.last_fingerprint_id = None
        self.last_confidence = 0
        self.last_logged_time = 0.0
        self.last_logged_id = None
        self._apply_saved_settings()
        # lightweight profiler for UI hotspots
        self.profiler = PerfProfiler(enabled=bool(self.settings.get("enable_profiler", False)), logger=None)
        self.init_database()
        self.build_ui()
        if self.auto_detect_serial:
            self.after(500, self.auto_detect_serial_on_startup)

    def init_database(self):
        init_database()

    def _apply_saved_settings(self):
        self.settings = load_settings()
        self.port_var = None
        self.baud_var = None
        self._apply_settings_to_runtime()

    def _apply_settings_to_runtime(self):
        settings = self.settings or default_settings()
        if settings.get("theme"):
            try:
                self.after(100, lambda: apply_appearance_mode(
                    "Dark" if str(settings["theme"]).lower() == "dark" else "Light",
                    self,
                ))
            except Exception:
                pass
        self.serial_handler.auto_reconnect_enabled = bool(settings.get("auto_reconnect", True))
        # runtime flag for whether to auto-detect ESP32 on startup/refresh
        self.auto_detect_serial = bool(settings.get("auto_detect_serial", True))

    def save_current_settings(self):
        settings = {
            "com_port": self._get_selected_port(),
            "baud_rate": self._get_selected_baud_rate(),
            "cooldown": self.settings.get("cooldown", 10),
            "theme": "dark" if ctk.get_appearance_mode().lower() == "dark" else "light",
            "auto_reconnect": self.serial_handler.auto_reconnect_enabled,
            "auto_detect_serial": bool(self.settings.get("auto_detect_serial", True)),
            "compact_sidebar": bool(self.settings.get("compact_sidebar", False)),
            "enable_profiler": bool(self.settings.get("enable_profiler", False)),
        }
        self.settings = settings
        save_settings(settings)
        return settings

    def _get_selected_port(self) -> str:
        port_var = getattr(self, "port_var", None)
        if port_var is None:
            return str((self.settings or {}).get("com_port", ""))
        value = port_var.get()
        return value.strip() if isinstance(value, str) else ""

    def _get_selected_baud_rate(self) -> int:
        baud_var = getattr(self, "baud_var", None)
        if baud_var is None:
            return int((self.settings or {}).get("baud_rate", CONFIG.baud_rate))
        value = baud_var.get()
        try:
            return int(value)
        except (TypeError, ValueError):
            return CONFIG.baud_rate

    def _apply_connection_ui_state(self, *, status_text: str, button_text: str, scan_state: str, stop_state: str, color: str):
        self.status_var.set(status_text)
        self.status_dot.configure(text_color=color)
        self.connect_button.configure(text=button_text)
        self.scan_button.configure(state=scan_state)
        self.stop_button.configure(state=stop_state)

    def _parse_attendance(self, message: str) -> None:
        """Handle legacy attendance parsing for compatibility with older workflows."""
        if not isinstance(message, str):
            return

        message = message.strip()
        if not message:
            return

        if message.startswith("ID:"):
            try:
                self.last_fingerprint_id = int(message.split(":", 1)[1])
            except (ValueError, IndexError):
                self.last_fingerprint_id = None
            self.last_confidence = 0
            return

        if message.startswith("CONFIDENCE:"):
            try:
                self.last_confidence = int(message.split(":", 1)[1])
            except (ValueError, IndexError):
                self.last_confidence = 0

            if self.last_fingerprint_id is None:
                return

            finger_id = self.last_fingerprint_id
            now = time.time()
            if self.last_logged_id == finger_id and self.last_logged_time > 0 and (now - self.last_logged_time) < 5:
                return

            self.last_logged_id = finger_id
            self.last_logged_time = now
            student = get_student(finger_id)
            status = "Present" if self.last_confidence >= CONFIG.min_confidence else "Weak Match"
            log_attendance(
                fingerprint_id=finger_id,
                confidence=self.last_confidence,
                status=status,
                now=datetime.now(),
            )
            self.log_message(f"Attendance logged for {student.get('student_name') if student else 'unknown'}")
            return

        if message == "UNKNOWN":
            self.last_fingerprint_id = 0
            self.last_confidence = 0
            return

        if self.last_fingerprint_id is None:
            return

        finger_id = self.last_fingerprint_id
        now = time.time()
        if self.last_logged_id == finger_id and self.last_logged_time > 0 and (now - self.last_logged_time) < 5:
            return

        self.last_logged_id = finger_id
        self.last_logged_time = now
        student = get_student(finger_id)
        status = "Present" if self.last_confidence >= CONFIG.min_confidence else "Weak Match"
        log_attendance(
            fingerprint_id=finger_id,
            confidence=self.last_confidence,
            status=status,
            now=datetime.now(),
        )
        self.log_message(f"Attendance logged for {student.get('student_name') if student else 'unknown'}")

    # ------------------------------------------------------------------
    # Role & Permissions
    # ------------------------------------------------------------------
    def has_permission(self, permission: str) -> bool:
        """Check if current user role has a specific permission."""
        role_config = CONFIG.user_roles.get(self.current_role, {})
        return permission in role_config.get("permissions", [])

    def update_button_permissions(self):
        """Update button states based on current user role."""
        self.enroll_button.configure(state="normal" if self.has_permission("enroll") else "disabled")
        self.wipe_button.configure(state="normal" if self.has_permission("wipe") else "disabled")
        self.backup_button.configure(state="normal" if self.has_permission("backup") else "disabled")
        self.restore_button.configure(state="normal" if self.has_permission("restore") else "disabled")

    def change_role(self, new_role: str):
        """Switch to a different user role and update permissions."""
        if new_role in CONFIG.user_roles:
            self.current_role = new_role
            self.update_button_permissions()
            role_name = CONFIG.user_roles[new_role].get("name", new_role)
            self.log_message(f"🔐 Switched to {role_name} role")
            if hasattr(self, "role_label"):
                self.role_label.configure(text=f"👤 {role_name}")

    def _on_role_changed(self, choice: str):
        """Handle role dropdown selection."""
        # Find the role key that matches the selected role name
        for role_key, role_config in CONFIG.user_roles.items():
            if role_config.get("name", role_key) == choice:
                self.change_role(role_key)
                break

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def build_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = self.build_sidebar()
        self.build_main_area()
        self.refresh_serial_ports(initial=True)

    def build_sidebar(self):
        return build_sidebar(self)

    def switch_page(self, page_name: str):
        if page_name == "dashboard":
            self.dashboard_page.refresh()
        elif page_name == "students":
            self.students_page.refresh()
        elif page_name == "settings":
            self.settings_page.refresh()

    def build_main_area(self):
        main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=max(10, int(16 * self.scaling_factor)), pady=max(10, int(16 * self.scaling_factor)))
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        # --- Header with role selector ---
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        # Role selector on the right
        role_frame = ctk.CTkFrame(header, fg_color="transparent")
        role_frame.grid(row=0, column=1, sticky="e")

        role_names = list(CONFIG.user_roles.keys())
        role_labels = [CONFIG.user_roles[role].get("name", role) for role in role_names]

        self.role_label = ctk.CTkLabel(
            role_frame, text=f"👤 {CONFIG.user_roles[self.current_role].get('name', self.current_role)}",
            font=("Segoe UI", 11), text_color=COLOR_ACCENT
        )
        self.role_label.grid(row=0, column=0, padx=(0, 8), sticky="e")

        self.role_dropdown = ctk.CTkComboBox(
            role_frame, values=role_labels, state="readonly",
            width=max(90, int(120 * self.scaling_factor)), command=self._on_role_changed
        )
        self.role_dropdown.set(CONFIG.user_roles[self.current_role].get("name", self.current_role))
        self.role_dropdown.grid(row=0, column=1, sticky="e")

        # Tabview below
        self.tabview = ctk.CTkTabview(main)
        self.tabview.configure(height=max(480, int(640 * self.scaling_factor)))
        self.tabview.grid(row=1, column=0, sticky="nsew")
        self.tabview.add("📅 Attendance")
        self.tabview.add("📊 Statistics")
        self.tabview.add("🖥 Live Log")

        self.attendance_page.build(self.tabview.tab("📅 Attendance"))
        build_statistics_tab(self, self.tabview.tab("📊 Statistics"))
        build_log_tab(self, self.tabview.tab("🖥 Live Log"))

    def _on_attendance_mode_changed(self, choice: str):
        self.attendance_mode = choice
        # Reset pagination when switching to Recent
        if choice == "Recent":
            self.attendance_offset = 0
        self.refresh_attendance_view()

    def _update_load_more_visibility(self):
        button = getattr(self, 'load_more_button', None)
        if button is None:
            return
        if getattr(self, 'attendance_mode', 'Today') == 'Recent':
            button.configure(state='normal')
        else:
            button.configure(state='disabled')

    def refresh_statistics(self, switch_tab: bool = False):
        """Refresh the statistics display.

        By default, this updates the statistics tab contents without switching the
        visible tab. Set switch_tab=True when the user explicitly requested stats.
        """
        if not self._ui_ready():
            return

        try:
            statistics_tab = self.tabview.tab("📊 Statistics")
            for child in statistics_tab.winfo_children():
                child.destroy()
            build_statistics_tab(self, statistics_tab)
            if switch_tab:
                self.tabview.set("📊 Statistics")
            self.log_message("Statistics refreshed")
        except Exception as e:
            self.log_message(f"Could not refresh statistics: {e}")

    def show_statistics_report(self):
        reports_page.show_statistics_report(self)

    def export_statistics_report(self):
        reports_page.export_statistics_report(self)

    def show_statistics_charts(self):
        reports_page.show_statistics_charts(self)

    # ------------------------------------------------------------------
    # Connection / scanning
    # ------------------------------------------------------------------
    def toggle_connection(self):
        if self.serial_handler.connected:
            self.stop_reader_thread()
            self.serial_handler.disconnect()
            self._set_disconnected_ui()
            self.log_message("Disconnected from ESP32.")
            return

        port = self._get_selected_port()
        if not port:
            self.log_message("Please choose a COM port before connecting.")
            self.log_message(build_serial_troubleshooting_message(self.serial_handler.list_available_ports()))
            return

        baud = self._get_selected_baud_rate()

        self.save_current_settings()

        ok, msg = self.serial_handler.connect(port, baud)
        if ok:
            self._on_serial_connected(port, baud)
        else:
            self._on_serial_connection_failed(msg)

    def _set_connected_ui(self):
        if getattr(self, '_closing', False):
            return
        self._apply_connection_ui_state(
            status_text="Connected",
            button_text="Disconnect",
            scan_state="normal",
            stop_state="disabled",
            color=COLOR_CONNECTED,
        )

    def _on_serial_connected(self, port: str, baud: int):
        self._set_connected_ui()
        self.log_message(f"Connected to ESP32 on {port} at {baud} baud")
        self.start_reader_thread()

    def _on_serial_connection_failed(self, msg: str):
        self._set_disconnected_ui()
        self.status_var.set("Connection failed")
        self.status_dot.configure(text_color=COLOR_DISCONNECTED)
        self.log_message(f"Connection failed: {msg}")
        self.log_message(build_serial_troubleshooting_message(self.serial_handler.list_available_ports()))

    def refresh_serial_ports(self, initial: bool = False):
        try:
            ports = self.serial_handler.list_available_ports() or []
            current_value = self._get_selected_port()

            if ports:
                if current_value not in ports:
                    current_value = ports[0]
                    if hasattr(self, "port_var"):
                        self.port_var.set(current_value)
                if hasattr(self, "port_combobox"):
                    self.port_combobox.configure(values=ports)
                if initial and hasattr(self, "port_var") and self.port_var.get() not in ports:
                    self.port_var.set(ports[0])
            else:
                fallback = current_value or "COM5"
                if hasattr(self, "port_combobox"):
                    self.port_combobox.configure(values=[fallback])
            if not initial:
                self.log_message(f"Serial ports refreshed: {', '.join(ports) if ports else 'none found'}")
            if not ports:
                self.log_message(build_serial_troubleshooting_message([]))
            if self.auto_detect_serial and ports and not initial and not getattr(self, "_auto_detect_in_progress", False):
                self.auto_detect_serial_on_startup()
        except Exception as e:
            self.log_message(f"Could not refresh serial ports: {e}")

    def open_settings_dialog(self):
        open_settings_dialog(self)

    def show_serial_help(self):
        message = build_serial_troubleshooting_message(self.serial_handler.list_available_ports())
        self.log_message("Opened ESP32 connection help")
        dialog = ctk.CTkToplevel(self)
        dialog.title("ESP32 Connection Help")
        dialog.geometry("720x420")
        dialog.transient(self)
        dialog.grab_set()

        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(content, text="ESP32 Connection Help", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 8))
        ctk.CTkLabel(content, text=message, justify="left", wraplength=660).pack(anchor="w", pady=(0, 12))

        button_row = ctk.CTkFrame(content, fg_color="transparent")
        button_row.pack(fill="x", pady=(8, 0))

        ctk.CTkButton(button_row, text="Open Device Manager", command=open_device_manager).pack(side="left", padx=(0, 8))
        ctk.CTkButton(button_row, text="Open Driver Help", command=open_driver_help).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            button_row,
            text="Try Common Ports",
            command=lambda: self.try_common_serial_ports(dialog),
        ).pack(side="left")
        ctk.CTkButton(button_row, text="Close", command=dialog.destroy).pack(side="right")

    def auto_detect_serial_on_startup(self):
        if getattr(self, '_closing', False) or getattr(self, '_auto_detect_in_progress', False):
            return False
        self._auto_detect_in_progress = True
        try:
            if getattr(self, 'serial_handler', None) and self.serial_handler.connected:
                return True
            self.refresh_serial_ports(initial=True)
            return self.try_common_serial_ports()
        except Exception as exc:
            self.log_message(f"Startup auto-detect failed: {exc}")
            return False
        finally:
            self._auto_detect_in_progress = False

    def try_common_serial_ports(self, dialog=None):
        if not self.serial_handler.pyserial_installed:
            self.log_message("pyserial is not installed; serial auto-detect is disabled.")
            return False

        ports = self.serial_handler.list_available_ports() or []
        candidates = build_common_port_candidates(ports)
        for port in candidates:
            try:
                baud = self._get_selected_baud_rate()
                ok, msg = self.serial_handler.connect(port, baud)
                if ok:
                    self.port_var.set(port)
                    self.save_current_settings()
                    self._on_serial_connected(port, baud)
                    self.log_message(f"Auto-detected ESP32 on {port} at {baud} baud")
                    if dialog is not None and dialog.winfo_exists():
                        dialog.destroy()
                    return True
                self.log_message(f"Auto-detect connect failed for {port}: {msg}")
            except Exception:
                continue
        self.log_message("No common COM port worked for the ESP32. Try the manual steps above.")
        return False

    def _set_disconnected_ui(self):
        if getattr(self, '_closing', False):
            return
        self._apply_connection_ui_state(
            status_text="Disconnected",
            button_text="Connect",
            scan_state="disabled",
            stop_state="disabled",
            color=COLOR_DISCONNECTED,
        )

    def _set_reconnect_ui(self):
        if getattr(self, '_closing', False):
            return
        self._apply_connection_ui_state(
            status_text="Reconnecting",
            button_text="Disconnect",
            scan_state="disabled",
            stop_state="disabled",
            color=COLOR_DISCONNECTED,
        )

    def _set_scan_mode_ui(self):
        if getattr(self, '_closing', False):
            return
        self.scan_mode_active = True
        self.enroll_mode_active = False
        self.wipe_mode_active = False
        self.enroll_button.configure(state="disabled")
        self.scan_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

    def _set_command_mode_ui(self):
        if getattr(self, '_closing', False):
            return
        self.scan_mode_active = False
        self.enroll_mode_active = False
        self.wipe_mode_active = False
        self.enroll_button.configure(state="normal" if self.has_permission("enroll") else "disabled")
        self.scan_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def _set_enroll_mode_ui(self):
        if getattr(self, '_closing', False):
            return
        self.enroll_mode_active = True
        self.scan_mode_active = False
        self.wipe_mode_active = False
        self.scan_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")
        self.enroll_button.configure(state="disabled")

    def _set_wipe_mode_ui(self):
        if getattr(self, '_closing', False):
            return
        self.wipe_mode_active = True
        self.scan_mode_active = False
        self.enroll_mode_active = False
        self.scan_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")
        self.enroll_button.configure(state="disabled")
        self.wipe_button.configure(state="disabled")

    def _clear_enroll_mode_ui(self):
        if getattr(self, '_closing', False):
            return
        self.enroll_mode_active = False
        if self.serial_handler.connected and not self.scan_mode_active and not self.wipe_mode_active:
            self._set_command_mode_ui()
        if self.has_permission("enroll") and getattr(self, 'enroll_button', None):
            self.enroll_button.configure(state="normal")

    def _parse_connection_mode(self, message):
        if not isinstance(message, str):
            return

        parsed = parse_json_line(message)
        if parsed is not None and parsed.get("type") == "status":
            state = parsed.get("state")
            if state == "SCAN_MODE":
                self._set_scan_mode_ui()
                return
            if state == "CMD_MODE":
                self._set_command_mode_ui()
                return

        if RE_SCAN_MODE.search(message):
            self._set_scan_mode_ui()
        elif RE_CMD_MODE.search(message):
            self._set_command_mode_ui()

    def _schedule_attendance_refresh(self):
        if not self._ui_ready():
            return
        try:
            self.after(150, self._refresh_attendance_view_safe)
        except Exception:
            self._refresh_attendance_view_safe()

    def _refresh_attendance_view_safe(self):
        if not self._ui_ready():
            return
        try:
            self.refresh_attendance_view()
            if self.tabview.get() == "📊 Statistics":
                self.refresh_statistics()
        except Exception:
            pass

    def start_scan(self):
        if self.enroll_dialog is not None and self.enroll_dialog.winfo_exists():
            self.log_message("Close or cancel the active enrollment before starting scan mode.")
            return

        # If wipe is active but enroll is not, block starting scan
        if self.wipe_mode_active and not self.enroll_mode_active:
            self.log_message("Cannot start scan while wipe is active.")
            return

        # If enroll mode is active, check whether an enroll dialog exists
        if self.enroll_mode_active:
            if self.enroll_dialog is not None and getattr(self.enroll_dialog, "winfo_exists", lambda: False)():
                self.log_message("Close or cancel the active enrollment before starting scan mode.")
                return
            # No active enroll dialog — treat as stale state. Clear enroll and any wipe flag and proceed.
            self.enroll_mode_active = False
            self.wipe_mode_active = False
            self.log_message("Cleared stale enroll/wipe state before starting scan mode.")

        if not self.serial_handler.connected:
            self.log_message("Please connect first.")
            return

        if cmd_scan(self.serial_handler):
            if hasattr(self, "_set_scan_mode_ui"):
                self._set_scan_mode_ui()
            else:
                self.scan_mode_active = True
                self.enroll_mode_active = False
                self.wipe_mode_active = False
            self.log_message("Sent SCAN command to ESP32.")
        else:
            self.log_message("Failed to send SCAN command to ESP32.")

    def stop_scan(self):
        if not self.serial_handler.connected:
            return
        if cmd_stop(self.serial_handler):
            self.scan_mode_active = False
            self.stop_button.configure(state="disabled")
            self.scan_button.configure(state="normal")
            self.enroll_button.configure(state="normal" if self.has_permission("enroll") else "disabled")
            self.log_message("Sent STOP command to ESP32.")
        else:
            self.log_message("Failed to send STOP command to ESP32.")

    def start_reader_thread(self):
        if self.reader_thread and self.reader_thread.is_alive():
            return
        self.stop_event.clear()
        self.reader_thread = threading.Thread(target=self.read_serial_output, daemon=True)
        self.reader_thread.start()

    def stop_reader_thread(self):
        self.stop_event.set()
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.0)
            self.reader_thread = None

    def read_serial_output(self):
        last_reconnect_count = 0
        while not self.stop_event.is_set():
            line = self.serial_handler.read_line()
            if not self.serial_handler.connected:
                # Check if auto-reconnect is in progress
                if self.serial_handler.reconnect_count > 0:
                    if self.serial_handler.reconnect_count != last_reconnect_count:
                        last_reconnect_count = self.serial_handler.reconnect_count
                        status_text = f"Reconnecting... ({self.serial_handler.reconnect_count}/{CONFIG.reconnect_max_retries})"
                        self.after(0, lambda text=status_text: self.status_var.set(text))
                        self.after(0, self._set_reconnect_ui)
                else:
                    self.after(0, self._set_disconnected_ui)
                time.sleep(0.2)
                continue

            # Reset reconnect counter on successful connection
            if last_reconnect_count > 0:
                last_reconnect_count = 0
                self.after(0, self._set_connected_ui)

            if line is None:
                time.sleep(0.05)
                continue
            if line:
                self.log_message(f"ESP32: {line}")

    def enroll_sample(self):
        if self.enroll_dialog is not None and self.enroll_dialog.winfo_exists():
            self.enroll_dialog.lift()
            self.enroll_dialog.focus()
            return

        if not self.serial_handler.connected:
            self.log_message("Please connect first.")
            return

        if self.enroll_mode_active:
            self.log_message("An enrollment is already in progress.")
            return

        if self.wipe_mode_active:
            self.log_message("Cannot enroll while a wipe operation is active.")
            return

        if self.scan_mode_active or getattr(self.stop_button, "cget", lambda x: "disabled")("state") == "normal":
            if cmd_stop(self.serial_handler):
                self.scan_mode_active = False
                self.stop_button.configure(state="disabled")
                self.log_message("Sent STOP command to ESP32 before enrollment.")
            else:
                self.log_message("Failed to stop current scan before enrollment.")
                return

        if cmd_enroll(self.serial_handler):
            self.log_message("Sent ENROLL command to ESP32. The ESP32 will use the next free ID.")
            self._set_enroll_mode_ui()
            self.open_enroll_dialog()
        else:
            self.log_message("Failed to send ENROLL command to ESP32.")

    def list_fingerprints(self):
        if self.serial_handler.connected:
            cmd_list(self.serial_handler)
            self.log_message("Sent LIST command to ESP32.")
        else:
            self.log_message("Not connected — showing saved student records only.")

        student_count = len(self.attendance_processor.all_students())
        self.log_message(f"{student_count} fingerprint(s) registered.")
        self.open_students_list_dialog()

    # ------------------------------------------------------------------
    # Enroll popup (profile form + live log side by side)
    # ------------------------------------------------------------------
    def open_enroll_dialog(self):
        return open_enroll_dialog(self)
    def save_enroll_profile(self):
        return save_enroll_profile(self)

    def close_enroll_dialog(self):
        if getattr(self, "enroll_mode_active", False) and getattr(self, "serial_handler", None) and self.serial_handler.connected:
            if cmd_stop(self.serial_handler):
                self.log_message("Sent STOP command to ESP32 when closing enrollment dialog.")
        result = close_enroll_dialog(self)
        self._clear_enroll_mode_ui()
        return result
    def _dispatch_attendance_message(self, message):
        if not isinstance(message, str):
            return

        result = self.attendance_processor.process_line(message)
        if result is None:
            return

        self._handle_scan_result(result)

    def _handle_scan_result(self, result):
        if not result.get("logged"):
            return

        fingerprint_id = int(result.get("fingerprint_id", 0) or 0)
        confidence = int(result.get("confidence", 0) or 0)
        status = result.get("status") or "UNKNOWN"
        timestamp = result.get("timestamp") or datetime.now()

        if fingerprint_id == 0:
            self.log_message(
                f"⚠ Unknown fingerprint scanned — saved to attendance log ({timestamp.strftime('%Y-%m-%d %H:%M:%S')})"
            )
            record = {
                'fingerprint_id': 0,
                'student_no': 'N/A',
                'student_name': None,
                'grade': 'N/A',
                'section': 'N/A',
                'date': timestamp.strftime('%Y-%m-%d'),
                'time': timestamp.strftime('%H:%M:%S'),
                'confidence': 0,
                'status': 'UNKNOWN',
            }
            self._render_attendance_record(record)
            return

        student = self.attendance_processor.lookup_student(fingerprint_id)
        if student:
            self.log_message(
                f"✓ Attendance logged: {student.get('student_name', 'Unknown')} (ID {fingerprint_id}, confidence {confidence})"
            )
        else:
            self.log_message(
                f"✓ Attendance logged for unknown fingerprint ID {fingerprint_id} (confidence {confidence})"
            )

        record = {
            'fingerprint_id': fingerprint_id,
            'student_no': student.get('student_no') if student else 'N/A',
            'student_name': student.get('student_name') if student else None,
            'grade': student.get('grade') if student else 'N/A',
            'section': student.get('section') if student else 'N/A',
            'date': timestamp.strftime('%Y-%m-%d'),
            'time': timestamp.strftime('%H:%M:%S'),
            'confidence': confidence,
            'status': 'Present',
        }
        self._render_attendance_record(record, has_student_profile=student is not None)

    def _render_attendance_record(self, record, has_student_profile=False):
        display = format_attendance_display(record)
        display['has_student_profile'] = has_student_profile

        try:
            today_str = datetime.now().strftime('%Y-%m-%d')
            attendance_mode = getattr(self, 'attendance_mode', 'Today')
            attendance_offset = getattr(self, 'attendance_offset', 0)

            if self.tabview.get() == "📅 Attendance":
                if attendance_mode == 'Today' and record['date'] == today_str:
                    self.after(0, lambda d=display: build_attendance_card(self, d, prepend=True))
                    self.after(0, self.refresh_attendance_view)
                elif attendance_mode == 'Recent' and attendance_offset == 0:
                    self.after(0, lambda d=display: build_attendance_card(self, d, prepend=True))
                    self.after(0, self.refresh_attendance_view)
        except Exception:
            self.after(0, self.refresh_attendance_view)

    def _parse_enroll_progress(self, message):
        """Watch ESP32 output for enroll-progress lines and reflect them in the popup."""
        if self.enroll_dialog is None or not self.enroll_dialog.winfo_exists():
            return

        match = RE_ENROLLING_AS.search(message)
        if match:
            self.enroll_id_var.set(match.group(1))
            self.enroll_ready_to_save = False
            if self.enroll_save_button is not None:
                self.enroll_save_button.configure(state="disabled")
            self.enroll_status_var.set("Enrolling — follow the prompts on the sensor. Save is disabled until enrollment completes.")
            return

        match = RE_ENROLL_SUCCESS.search(message)
        if match:
            self.enroll_id_var.set(match.group(1))
            self.enroll_ready_to_save = True
            if self.enroll_save_button is not None:
                self.enroll_save_button.configure(state="normal")
            self.enroll_status_var.set(
                f"Fingerprint saved as ID {match.group(1)}. Fill in the student's details and Save."
            )
            return

        if RE_ENROLL_CANCEL.search(message):
            self.enroll_ready_to_save = False
            if self.enroll_save_button is not None:
                self.enroll_save_button.configure(state="disabled")
            self.enroll_status_var.set(
                "Enrollment cancelled. Close this dialog or start a new enrollment to try again."
            )
            return

        upper = message.upper()
        if "ERROR" in upper or "FAIL" in upper:
            self.enroll_status_var.set("Sensor reported an error — check the log on the right.")

    # ------------------------------------------------------------------
    # Wipe popup (confirmation + live log side by side)
    # ------------------------------------------------------------------
    def open_wipe_dialog(self):
        self._set_wipe_mode_ui()
        return open_wipe_dialog(self)
    def confirm_wipe(self):
        return confirm_wipe(self)

    def close_wipe_dialog(self):
        result = close_wipe_dialog(self)
        self.wipe_mode_active = False
        if self.serial_handler.connected and not self.scan_mode_active:
            self._set_command_mode_ui()
        if self.has_permission("wipe") and getattr(self, 'wipe_button', None):
            self.wipe_button.configure(state="normal")
        return result
    def _parse_wipe_progress(self, message):
        """Watch ESP32 output for wipe-progress lines and reflect them in the popup."""
        if self.wipe_dialog is None or not self.wipe_dialog.winfo_exists():
            return
        if self.wipe_status_var is None:
            return

        if RE_WIPE_START.search(message):
            self.wipe_status_var.set("Wiping… please wait.")
            return

        if RE_WIPE_SUCCESS.search(message):
            student_count, attendance_count = self._clear_database_data()
            self.wipe_status_var.set(
                f"✅ All fingerprints wiped. Cleared {student_count} student profile(s) and {attendance_count} attendance record(s)."
            )
            if self.wipe_confirm_button is not None and self.wipe_confirm_button.winfo_exists():
                self.wipe_confirm_button.configure(state="normal")
            return

        upper = message.upper()
        if "ERROR" in upper or "FAIL" in upper:
            self.wipe_status_var.set("Sensor reported an error — check the log on the right.")
            if self.wipe_confirm_button is not None and self.wipe_confirm_button.winfo_exists():
                self.wipe_confirm_button.configure(state="normal")

    # ------------------------------------------------------------------
    # Student roster popup (opened from "List") + Edit popup
    # ------------------------------------------------------------------
    def open_students_list_dialog(self):
        return open_students_list_dialog(self)
    def close_students_dialog(self):
        return close_students_dialog(self)


    def _clear_database_data(self):
        """Deletes every student profile and attendance record from the database."""
        student_count, attendance_count = clear_all_data()
        self.refresh_student_list()
        self.refresh_attendance_view()
        self.refresh_statistics()
        if student_count or attendance_count:
            self.log_message(
                f"Cleared {student_count} student profile(s) and {attendance_count} attendance record(s) from the database."
            )
        return student_count, attendance_count

    def refresh_student_list(self):
        return self.students_page.refresh()

    def delete_student_from_list(self, fingerprint_id, parent=None):
        return self.students_page.delete_student(fingerprint_id, parent=parent)
    def open_edit_dialog(self, fingerprint_id):
        return self.students_page.open_edit_dialog(fingerprint_id)

    def backup_database(self):
        """Create a database backup."""
        try:
            success, message, path = backup_database_service()
            if success:
                self.log_message(f"✓ {message}")
                messagebox.showinfo("Backup Successful", f"{message}\n\nBackup saved at:\n{path}")
            else:
                self.log_message(f"✗ Backup failed: {message}")
                messagebox.showerror("Backup Failed", message)
        except Exception as e:
            self.log_message(f"✗ Error: {e}")
            messagebox.showerror("Error", f"Backup error: {e}")

    def open_restore_dialog(self):
        return open_restore_dialog(self)
    def quit_app(self):
        if getattr(self, "_closing", False):
            return
        self._closing = True
        self.stop_event.set()
        if self.serial_handler.connected:
            try:
                self.serial_handler.disconnect()
            except Exception:
                pass
        if self.winfo_exists():
            self.destroy()

    def _ui_ready(self):
        try:
            return not getattr(self, "_closing", False) and self.winfo_exists()
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Attendance / log
    # ------------------------------------------------------------------
    def toggle_attendance_view(self):
        self.refresh_attendance_view()

    def refresh_attendance_view(self):
        return self.attendance_page.refresh()

    def load_more_attendance(self):
        return self.attendance_page.load_more()

    def open_add_student_dialog(self, fingerprint_id: int):
        return self.students_page.open_add_student_dialog(fingerprint_id)

    def log_message(self, message):
        if self._ui_ready():
            self.after(0, self._append_log_message, message)

    def _append_log_message(self, message):
        if not self._ui_ready():
            return

        for widget in (
            getattr(self, "log_text", None),
            getattr(self, "enroll_log_text", None),
            getattr(self, "wipe_log_text", None),
        ):
            if widget is None:
                continue
            try:
                if widget.winfo_exists():
                    widget.configure(state="normal")
                    widget.insert("end", message + "\n")
                    widget.see("end")
                    widget.configure(state="disabled")
            except Exception:
                pass

        try:
            raw_message = message
            if isinstance(message, str) and message.startswith("ESP32:"):
                raw_message = message[len("ESP32:"):].strip()
            self._parse_connection_mode(raw_message)
            self._dispatch_attendance_message(raw_message)
            self._parse_enroll_progress(raw_message)
            self._parse_wipe_progress(raw_message)
        except Exception:
            pass

    def clear_log(self):
        if not self._ui_ready():
            return
        try:
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.insert("end", "Log cleared.\n")
            self.log_text.configure(state="disabled")
        except Exception:
            pass


def main():
    apply_default_theme(None)
    app = FingerprintApp()
    app.mainloop()


if __name__ == "__main__":
    main()
