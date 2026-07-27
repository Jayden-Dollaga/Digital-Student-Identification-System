import sys
import threading
import time
import re
import calendar
import tkinter as tk
from pathlib import Path
from datetime import datetime
from tkinter import messagebox, filedialog

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

import customtkinter as ctk

from config import COM_PORT, BAUD_RATE, BAUD_RATES, RECONNECT_MAX_RETRIES
from gui.layout_utils import resolve_window_size, resolve_sidebar_width
from core.serial_handler import SerialHandler
from settings_store import default_settings, load_settings, save_settings
from core.commands import cmd_scan, cmd_stop, cmd_enroll, cmd_delete, cmd_wipe, cmd_list
from gui.attendance_page import AttendancePage, build_attendance_tab, refresh_attendance_view, load_more_attendance, build_attendance_card
from gui.statistics_page import build_statistics_tab
from gui.log_page import build_log_tab
from gui.settings_dialog import open_settings_dialog
from gui.dialogs import open_enroll_dialog, save_enroll_profile, close_enroll_dialog, open_wipe_dialog, confirm_wipe, close_wipe_dialog, open_restore_dialog
from gui import reports_page
from gui.students_page import (
    StudentsPage,
    open_students_list_dialog,
    refresh_student_list,
    delete_student_from_list,
    open_edit_dialog,
    open_add_student_dialog,
)
from gui.dashboard import DashboardPage
from gui.settings_page import SettingsPage
from gui.theme import apply_default_theme, apply_appearance_mode
from gui.perf_profiler import PerfProfiler
from gui.serial_troubleshooting import build_serial_troubleshooting_message, build_common_port_candidates, open_device_manager, open_driver_help
from core.database import (
    init_database,
    get_attendance_all,
    get_attendance_today,
    register_student,
    get_all_students,
    get_student,
    delete_student,
    clear_all_students,
    clear_all_data,
    backup_database as backup_database_service,
    restore_database,
    list_backups,
    log_attendance,
    get_attendance_paginated,
)
from core.utils import format_attendance_display

# Image handling for charts + sidebar avatars
try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

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

# ---- WHS dashboard theme (this is now the visual base for the whole app) ----
WHS_BG = "#eef1f7"
WHS_SIDEBAR_BG = "#141b2d"
WHS_SIDEBAR_ROW_ACTIVE = "#232e4d"
WHS_CARD_BG = "#ffffff"
WHS_TEXT_DARK = "#2b2f42"
WHS_TEXT_GRAY = "#9aa1b5"
WHS_BLUE = "#3aa0ff"
WHS_BLUE_LIGHT = "#eaf4ff"
WHS_GREEN = "#3ecf8e"
WHS_GREEN_LIGHT = "#e6faf1"
WHS_RED = "#ff6b81"
WHS_RED_LIGHT = "#ffeef1"
WHS_ORANGE = "#ff8a5b"
WHS_AVATAR_PALETTE = ["#7c8ce0", "#e07c9a", "#e0a97c", "#7cc7e0", "#a37ce0", "#7ce0a0"]


def make_circle_avatar(initials, color, size=40):
    """Generate a circular PIL avatar with initials — used for the sidebar
    student roster and any per-person indicators in the WHS-style shell."""
    if not PILLOW_AVAILABLE:
        return None
    scale = 4
    big = size * scale
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, big, big), fill=color)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(big * 0.4)
        )
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), initials, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((big - w) / 2 - bbox[0], (big - h) / 2 - bbox[1]), initials, font=font, fill="white")
    return img.resize((size, size), Image.LANCZOS)

# ESP32 output patterns that drive the enroll popup
RE_ENROLLING_AS = re.compile(r"ENROLLING FINGER AS ID #(\d+)", re.IGNORECASE)
RE_ENROLL_SUCCESS = re.compile(r"SUCCESS!?\s*Finger saved as ID #(\d+)", re.IGNORECASE)
RE_ENROLL_CANCEL = re.compile(r"ENROLLMENT cancelled|Enrollment cancelled|ENROLL_CANCELLED", re.IGNORECASE)

# ESP32 output patterns that drive the wipe popup
RE_WIPE_START = re.compile(r"Wiping ALL fingerprints", re.IGNORECASE)
RE_WIPE_SUCCESS = re.compile(r"SUCCESS\s*-\s*All fingerprints deleted", re.IGNORECASE)

# ESP32 output patterns for attendance logging
RE_ID_FOUND = re.compile(r"^ID[:\s]+(\d+)\s*$", re.IGNORECASE)
RE_CONFIDENCE = re.compile(r"^CONFIDENCE[:\s]+(\d+)\s*$", re.IGNORECASE)
RE_UNKNOWN = re.compile(r"^UNKNOWN\s*$", re.IGNORECASE)
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
        self.minsize(960, 600)

        self.scaling_factor = 1.0
        ctk.set_default_color_theme("blue")
        ctk.set_appearance_mode("light")
        self.configure(fg_color=WHS_BG)

        self.serial_handler = SerialHandler()
        self.stop_event = threading.Event()
        self.reader_thread = None
        self.scan_mode_active = False
        self.enroll_mode_active = False
        self.wipe_mode_active = False
        self._closing = False
        self._avatar_cache = []  # keep CTkImage refs alive for the WHS sidebar roster
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

        # Attendance tracking state (for auto-logging)
        self.last_fingerprint_id = None        # Most recently detected fingerprint ID
        self.last_id_time = 0                  # When it was detected
        self.ID_TIMEOUT = 2.0                  # Seconds before an ID expires without confidence
        self.last_confidence = 0               # Its confidence value
        self.last_logged_times = {}            # Per-fingerprint cooldown tracking
        self.last_unknown_time = 0             # Tracks the last unknown scan time for throttling

        # User role system
        from config import DEFAULT_USER_ROLE
        self.current_role = DEFAULT_USER_ROLE

        self.dashboard_page = DashboardPage(self)
        self.students_page = StudentsPage(self)
        self.attendance_page = AttendancePage(self)
        self.settings_page = SettingsPage(self)

        self._apply_saved_settings()
        # lightweight profiler for UI hotspots
        self.profiler = PerfProfiler(enabled=bool(self.settings.get("enable_profiler", False)), logger=None)
        self.init_database()
        self.build_ui()
        if self.auto_detect_serial:
            self.after(500, self.auto_detect_serial_on_startup)

    def init_database(self):
        try:
            init_database()
            self.db_ready = True
        except Exception as e:
            self.db_ready = False
            self.log_message(f"✗ Database init failed: {e}")

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
            "com_port": self.port_var.get().strip() if getattr(self, "port_var", None) else self.settings.get("com_port", ""),
            "baud_rate": int(self.baud_var.get()) if getattr(self, "baud_var", None) and self.baud_var.get() else self.settings.get("baud_rate", BAUD_RATE),
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

    # ------------------------------------------------------------------
    # Role & Permissions
    # ------------------------------------------------------------------
    def has_permission(self, permission: str) -> bool:
        """Check if current user role has a specific permission."""
        from config import USER_ROLES
        role_config = USER_ROLES.get(self.current_role, {})
        return permission in role_config.get("permissions", [])

    def update_button_permissions(self):
        """Update button states based on current user role."""
        self.enroll_button.configure(state="normal" if self.has_permission("enroll") else "disabled")
        self.wipe_button.configure(state="normal" if self.has_permission("wipe") else "disabled")
        self.backup_button.configure(state="normal" if self.has_permission("backup") else "disabled")
        self.restore_button.configure(state="normal" if self.has_permission("restore") else "disabled")

    def change_role(self, new_role: str):
        """Switch to a different user role and update permissions."""
        from config import USER_ROLES
        if new_role in USER_ROLES:
            self.current_role = new_role
            self.update_button_permissions()
            role_name = USER_ROLES[new_role].get("name", new_role)
            self.log_message(f"🔐 Switched to {role_name} role")
            if hasattr(self, "role_label"):
                self.role_label.configure(text=f"👤 {role_name}")

    def _on_role_changed(self, choice: str):
        """Handle role dropdown selection."""
        from config import USER_ROLES
        # Find the role key that matches the selected role name
        for role_key, role_config in USER_ROLES.items():
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

    def switch_page(self, page_name: str):
        if page_name == "dashboard":
            self.dashboard_page.refresh()
        elif page_name == "students":
            self.students_page.refresh()
        elif page_name == "settings":
            self.settings_page.refresh()

    # ==================================================================
    # WHS-styled sidebar — this replaces the old gui.sidebar.build_sidebar
    # import (that module wasn't available to merge), but exposes the exact
    # same attribute names the rest of this file already relies on:
    # port_var, baud_var, port_combobox, connect_button, scan_button,
    # stop_button, enroll_button, wipe_button, backup_button, restore_button,
    # status_var, status_dot, role_label, role_dropdown.
    # ==================================================================
    def build_sidebar(self):
        try:
            sidebar_width = resolve_sidebar_width(self._screen_width)
        except Exception:
            sidebar_width = 250

        sidebar = ctk.CTkFrame(self, width=sidebar_width, fg_color=WHS_SIDEBAR_BG, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        # --- Logo -----------------------------------------------------
        ctk.CTkLabel(
            sidebar, text="🫆 Fingerprint AMS", text_color=WHS_BLUE,
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(20, 14), padx=16)

        # --- Connection card -------------------------------------------
        conn_card = ctk.CTkFrame(sidebar, fg_color=WHS_SIDEBAR_ROW_ACTIVE, corner_radius=10)
        conn_card.pack(fill="x", padx=14, pady=(0, 12))

        status_row = ctk.CTkFrame(conn_card, fg_color="transparent")
        status_row.pack(fill="x", padx=12, pady=(10, 4))
        self.status_dot = ctk.CTkLabel(status_row, text="●", text_color=COLOR_DISCONNECTED,
                                        font=("Segoe UI", 14))
        self.status_dot.pack(side="left")
        self.status_var = ctk.StringVar(value="Disconnected")
        ctk.CTkLabel(status_row, textvariable=self.status_var, text_color="white",
                     font=("Segoe UI", 11, "bold")).pack(side="left", padx=(6, 0))

        self.port_var = ctk.StringVar(value=self.settings.get("com_port", "") or COM_PORT)
        self.port_combobox = ctk.CTkComboBox(
            conn_card, variable=self.port_var, values=[self.port_var.get()],
            width=sidebar_width - 48, height=28
        )
        self.port_combobox.pack(padx=12, pady=4)

        self.baud_var = ctk.StringVar(value=str(self.settings.get("baud_rate", BAUD_RATE)))
        ctk.CTkComboBox(
            conn_card, variable=self.baud_var, values=[str(b) for b in BAUD_RATES],
            width=sidebar_width - 48, height=28
        ).pack(padx=12, pady=(0, 8))

        self.connect_button = ctk.CTkButton(
            conn_card, text="Connect", command=self.toggle_connection,
            fg_color=WHS_BLUE, hover_color="#2c8ce0", corner_radius=8, height=30
        )
        self.connect_button.pack(fill="x", padx=12, pady=(0, 10))

        # --- Action buttons ---------------------------------------------
        actions = ctk.CTkFrame(sidebar, fg_color="transparent")
        actions.pack(fill="x", padx=14, pady=(0, 12))

        def action_btn(parent, text, command, color, state="normal"):
            b = ctk.CTkButton(
                parent, text=text, command=command, fg_color=color,
                corner_radius=8, height=30, font=("Segoe UI", 11, "bold"), state=state
            )
            b.pack(fill="x", pady=3)
            return b

        self.scan_button = action_btn(actions, "▶  Scan", self.start_scan, WHS_GREEN, state="disabled")
        self.stop_button = action_btn(actions, "■  Stop", self.stop_scan, WHS_ORANGE, state="disabled")
        self.enroll_button = action_btn(actions, "➕  Enroll", self.enroll_sample, WHS_BLUE)
        action_btn(actions, "📋  List Fingerprints", self.list_fingerprints, "#5b6785")
        self.wipe_button = action_btn(actions, "🗑  Wipe All", self.open_wipe_dialog, WHS_RED)
        self.backup_button = action_btn(actions, "💾  Backup", self.backup_database, "#5b6785")
        self.restore_button = action_btn(actions, "♻  Restore", self.open_restore_dialog, "#5b6785")

        # --- Role selector -----------------------------------------------
        from config import USER_ROLES
        role_names = list(USER_ROLES.keys())
        role_labels = [USER_ROLES[role].get("name", role) for role in role_names]

        role_box = ctk.CTkFrame(sidebar, fg_color="transparent")
        role_box.pack(fill="x", padx=14, pady=(0, 12))
        self.role_label = ctk.CTkLabel(
            role_box, text=f"👤 {USER_ROLES[self.current_role].get('name', self.current_role)}",
            font=("Segoe UI", 11), text_color=WHS_TEXT_GRAY
        )
        self.role_label.pack(anchor="w", pady=(0, 4))
        self.role_dropdown = ctk.CTkComboBox(
            role_box, values=role_labels, state="readonly", command=self._on_role_changed
        )
        self.role_dropdown.set(USER_ROLES[self.current_role].get("name", self.current_role))
        self.role_dropdown.pack(fill="x")

        ctk.CTkFrame(sidebar, fg_color="#2a3350", height=1).pack(fill="x", padx=20, pady=(4, 10))

        # --- Registered students roster (real data, not mock) -------------
        ctk.CTkLabel(
            sidebar, text="Registered Students", text_color=WHS_TEXT_GRAY,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=20, pady=(0, 6))

        self.student_roster_frame = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        self.student_roster_frame.pack(fill="both", expand=True, padx=8)
        self.refresh_student_roster()

        return sidebar

    def _avatar(self, initials, color_idx=0, size=34):
        if not PILLOW_AVAILABLE:
            return None
        pil_img = make_circle_avatar(initials, WHS_AVATAR_PALETTE[color_idx % len(WHS_AVATAR_PALETTE)], size)
        img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(size, size))
        self._avatar_cache.append(img)
        return img

    def refresh_student_roster(self):
        """Rebuilds the sidebar roster from the real student table."""
        frame = getattr(self, "student_roster_frame", None)
        if frame is None or not frame.winfo_exists():
            return
        for child in frame.winfo_children():
            child.destroy()

        try:
            students = get_all_students() or []
        except Exception as e:
            ctk.CTkLabel(frame, text=f"Could not load students: {e}", text_color=WHS_RED,
                         wraplength=180, font=("Segoe UI", 10)).pack(pady=8)
            return

        query = ""
        if hasattr(self, "header_search_var"):
            query = self.header_search_var.get().strip().lower()

        for i, student in enumerate(students):
            name = student.get("student_name") or "Unnamed"
            fid = student.get("fingerprint_id")
            section = student.get("section") or ""
            if query and query not in name.lower() and query not in str(fid):
                continue

            row = ctk.CTkFrame(frame, fg_color="transparent", corner_radius=8)
            row.pack(fill="x", pady=2)
            row.bind("<Button-1>", lambda e, f=fid: self.open_edit_dialog(f))

            initials = "".join([p[0] for p in name.split()[:2]]).upper() or "?"
            img = self._avatar(initials, i)
            if img is not None:
                av = ctk.CTkLabel(row, image=img, text="", fg_color="transparent")
                av.pack(side="left", padx=(6, 8), pady=4)
                av.bind("<Button-1>", lambda e, f=fid: self.open_edit_dialog(f))

            text_col = ctk.CTkFrame(row, fg_color="transparent")
            text_col.pack(side="left", fill="both", expand=True, pady=4)
            name_lbl = ctk.CTkLabel(text_col, text=name, text_color="white", anchor="w",
                                     font=("Segoe UI", 11, "bold"))
            name_lbl.pack(fill="x")
            name_lbl.bind("<Button-1>", lambda e, f=fid: self.open_edit_dialog(f))
            sub_lbl = ctk.CTkLabel(text_col, text=f"ID {fid} · {section}", text_color=WHS_TEXT_GRAY,
                                    anchor="w", font=("Segoe UI", 9))
            sub_lbl.pack(fill="x")

        if not students:
            ctk.CTkLabel(frame, text="No students enrolled yet.", text_color=WHS_TEXT_GRAY,
                         font=("Segoe UI", 10)).pack(pady=8)

    # ==================================================================
    # WHS-styled main area — header bar + card-wrapped tabview
    # ==================================================================
    def build_main_area(self):
        main = ctk.CTkFrame(self, corner_radius=0, fg_color=WHS_BG)
        main.grid(row=0, column=1, sticky="nsew", padx=max(10, int(16 * self.scaling_factor)), pady=max(10, int(16 * self.scaling_factor)))
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        # --- WHS-style status bar (search / notifications / clock / live status) ---
        self.build_whs_header(main)

        # --- Card-wrapped tabview ------------------------------------------
        content_card = ctk.CTkFrame(main, fg_color=WHS_CARD_BG, corner_radius=16)
        content_card.grid(row=1, column=0, sticky="nsew")
        content_card.grid_columnconfigure(0, weight=1)
        content_card.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(content_card, fg_color=WHS_CARD_BG)
        self.tabview.configure(height=max(480, int(640 * self.scaling_factor)))
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # "🏠 Dashboard" is the literal WHS mockup layout, wired to real data,
        # and is the default/first tab shown.
        self.tabview.add("🏠 Dashboard")
        self.build_dashboard_tab(self.tabview.tab("🏠 Dashboard"))

        # The original detailed attendance log/pagination is preserved here
        # rather than removed — nothing from your working AttendancePage is lost.
        self.tabview.add("📅 Attendance Log")
        self.attendance_page.build(self.tabview.tab("📅 Attendance Log"))

        self.tabview.add("📊 Statistics")
        build_statistics_tab(self, self.tabview.tab("📊 Statistics"))

        self.tabview.add("🖥 Live Log")
        build_log_tab(self, self.tabview.tab("🖥 Live Log"))

        # Settings genuinely embeds now — the real gui/settings_page.py has a
        # working .build(parent) method.
        self.tabview.add("⚙ Settings")
        self._safe_build_page_tab(
            self.settings_page, self.tabview.tab("⚙ Settings"),
            fallback_text="Open settings dialog",
            fallback_command=self.open_settings_dialog,
        )

        # Students is intentionally dialog-based — the real gui/students_page.py
        # has no .build(parent) method at all (open_list_dialog opens a
        # CTkToplevel popup), so this isn't a guess/fallback anymore, it's
        # just how that page actually works.
        self.tabview.add("🧑‍🎓 Students")
        self._safe_build_page_tab(
            self.students_page, self.tabview.tab("🧑‍🎓 Students"),
            fallback_text="Open Registered Students",
            fallback_command=self.open_students_list_dialog,
            dialog_only=True,
        )

        self.tabview.set("🏠 Dashboard")

    def _safe_build_page_tab(self, page_obj, tab, fallback_text, fallback_command, dialog_only=False):
        try:
            if hasattr(page_obj, "build"):
                page_obj.build(tab)
                return
        except Exception as e:
            self.log_message(f"Could not build page inline ({e}); showing fallback button.")

        message = (
            "Students are managed in their own window so the roster stays\n"
            "usable at any size — click below to open it."
            if dialog_only else
            "This page's layout couldn't be embedded here directly."
        )
        ctk.CTkLabel(tab, text=message, text_color=WHS_TEXT_GRAY, wraplength=400, justify="left").pack(pady=(30, 10))
        ctk.CTkButton(tab, text=fallback_text, command=fallback_command,
                      fg_color=WHS_BLUE, hover_color="#2c8ce0").pack()

    # ==================================================================
    # "🏠 Dashboard" — literal recreation of the whs_dashboard.py mockup,
    # wired to real students/attendance data instead of the mockup's fake
    # rows. Layout matches the mockup 1:1:
    #   Work Attendance grid  (top, full width)
    #   Abnormal Attendance Record cards  (bottom-left, wide)
    #   Need Work panel + System Status   (bottom-right, stacked)
    # ==================================================================
    def build_dashboard_tab(self, tab):
        outer = ctk.CTkFrame(tab, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=4, pady=4)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=1)

        attendance_card = ctk.CTkFrame(outer, fg_color=WHS_CARD_BG, corner_radius=16,
                                        border_width=1, border_color="#eef0f5")
        attendance_card.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        self._build_work_attendance_card(attendance_card)

        bottom = ctk.CTkFrame(outer, fg_color="transparent")
        bottom.grid(row=1, column=0, sticky="nsew")
        bottom.grid_columnconfigure(0, weight=3)
        bottom.grid_columnconfigure(1, weight=2)
        bottom.grid_rowconfigure(0, weight=1)

        abnormal_card = ctk.CTkFrame(bottom, fg_color=WHS_CARD_BG, corner_radius=16,
                                      border_width=1, border_color="#eef0f5")
        abnormal_card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self._build_abnormal_records_card(abnormal_card)

        right_col = ctk.CTkFrame(bottom, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew")
        right_col.grid_rowconfigure(0, weight=4)
        right_col.grid_rowconfigure(1, weight=3)
        right_col.grid_columnconfigure(0, weight=1)

        need_work_card = ctk.CTkFrame(right_col, fg_color=WHS_CARD_BG, corner_radius=16,
                                       border_width=1, border_color="#eef0f5")
        need_work_card.grid(row=0, column=0, sticky="nsew", pady=(0, 14))
        self._build_need_work_panel(need_work_card)

        status_card = ctk.CTkFrame(right_col, fg_color=WHS_CARD_BG, corner_radius=16,
                                    border_width=1, border_color="#eef0f5")
        status_card.grid(row=1, column=0, sticky="nsew")
        self.build_system_status_panel(status_card)

    # ---- Work Attendance grid (real data) --------------------------------
    def _compute_month_attendance_grid(self):
        """Builds {student: {...}, marks: {day: 'check'|'x'}} rows for every
        registered student for the current month, using real attendance
        records. A day is a check if a 'Present' scan exists for that
        student on that date; an x if the day is a school day (Mon–Fri)
        that has already passed with no scan; blank otherwise (weekend or
        a day that hasn't happened yet)."""
        today = datetime.now()
        try:
            students = get_all_students() or []
        except Exception as e:
            self.log_message(f"Could not load students for attendance grid: {e}")
            students = []

        try:
            raw_records = get_attendance_all() or []
        except Exception as e:
            self.log_message(f"Could not load attendance records: {e}")
            raw_records = []

        # Index real attendance by (fingerprint_id, day-of-month) for this month/year
        by_student_day = {}
        for rec in raw_records:
            try:
                d = rec.get("date") if isinstance(rec, dict) else None
                if not d:
                    continue
                y, m, day = [int(x) for x in d.split("-")]
                if y == today.year and m == today.month:
                    fid = rec.get("fingerprint_id")
                    status = (rec.get("status") or "").lower()
                    by_student_day.setdefault(fid, {})[day] = status
            except Exception:
                continue

        days_in_month = calendar.monthrange(today.year, today.month)[1]
        rows = []
        for student in students:
            fid = student.get("fingerprint_id")
            marks = {}
            for day in range(1, days_in_month + 1):
                day_date = datetime(today.year, today.month, day)
                if day_date.weekday() >= 5:  # Sat/Sun
                    continue
                if day_date.date() > today.date():
                    continue
                status = by_student_day.get(fid, {}).get(day)
                if status == "present":
                    marks[day] = "check"
                else:
                    marks[day] = "x"
            rows.append({
                "fingerprint_id": fid,
                "name": student.get("student_name") or f"ID {fid}",
                "marks": marks,
            })
        return rows, days_in_month

    def _build_work_attendance_card(self, parent):
        ctk.CTkLabel(parent, text="Work Attendance", text_color=WHS_TEXT_DARK,
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=18, pady=(14, 6))

        rows, days_in_month = self._compute_month_attendance_grid()

        cell_w = 22
        name_col_w = 170
        canvas_w = name_col_w + days_in_month * cell_w + 20
        row_h = 28
        header_h = 22
        visible_rows = min(len(rows), 8) or 1
        canvas_h = header_h + row_h * visible_rows + 10

        canvas_wrap = ctk.CTkFrame(parent, fg_color="transparent")
        canvas_wrap.pack(fill="x", padx=18, pady=(0, 6))
        canvas = tk.Canvas(canvas_wrap, width=canvas_w, height=canvas_h, bg=WHS_CARD_BG,
                            highlightthickness=0)
        canvas.pack(fill="x")

        today_day = datetime.now().day
        for d in range(1, days_in_month + 1):
            x = name_col_w + (d - 1) * cell_w
            weekday = datetime(datetime.now().year, datetime.now().month, d).weekday()
            if weekday >= 5:
                canvas.create_rectangle(x, 0, x + cell_w, canvas_h, fill="#fdf3e4", width=0)
            canvas.create_text(x + cell_w / 2, header_h / 2, text=str(d),
                                fill=WHS_TEXT_GRAY, font=("Helvetica", 7))

        canvas.create_text(16, header_h / 2, text="Name", fill=WHS_TEXT_GRAY,
                            font=("Helvetica", 9, "bold"), anchor="w")
        canvas.create_line(0, header_h, canvas_w, header_h, fill="#eef0f5")

        if not rows:
            canvas.create_text(canvas_w / 2, canvas_h / 2, text="No registered students yet",
                                fill=WHS_TEXT_GRAY, font=("Helvetica", 10))

        for r, row in enumerate(rows[:visible_rows]):
            y = header_h + r * row_h
            yc = y + row_h / 2
            canvas.create_text(16, yc, text=row["name"], fill=WHS_TEXT_DARK,
                                font=("Helvetica", 9), anchor="w")
            for day, mark in row["marks"].items():
                x = name_col_w + (day - 1) * cell_w + cell_w / 2
                if mark == "check":
                    canvas.create_oval(x - 7, yc - 7, x + 7, yc + 7, fill=WHS_GREEN_LIGHT, outline="")
                    canvas.create_text(x, yc, text="\u2713", fill=WHS_GREEN, font=("Helvetica", 8, "bold"))
                else:
                    canvas.create_oval(x - 7, yc - 7, x + 7, yc + 7, fill=WHS_RED_LIGHT, outline="")
                    canvas.create_text(x, yc, text="\u2715", fill=WHS_RED, font=("Helvetica", 8, "bold"))
            if r < visible_rows - 1:
                canvas.create_line(0, y + row_h, canvas_w, y + row_h, fill="#f3f4f8")

        if len(rows) > visible_rows:
            ctk.CTkLabel(parent, text=f"+ {len(rows) - visible_rows} more student(s) — see 📅 Attendance Log",
                         text_color=WHS_TEXT_GRAY, font=("Segoe UI", 10)).pack(anchor="w", padx=18)

        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(anchor="w", padx=18, pady=(4, 16))
        ctk.CTkButton(
            btn_row, text="🔄  Refresh Grid", command=self.refresh_dashboard_tab,
            fg_color=WHS_BLUE, hover_color="#2c8ce0", corner_radius=18, width=150, height=36,
            font=("Segoe UI", 12, "bold")
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            btn_row, text="⚠  Review Unknown Scans", command=lambda: self.tabview.set("🏠 Dashboard"),
            fg_color=WHS_ORANGE, hover_color="#e87a4b", corner_radius=18, width=190, height=36,
            font=("Segoe UI", 12, "bold")
        ).pack(side="left")

    # ---- Abnormal Attendance Record (real unresolved scans) ---------------
    def _get_abnormal_records(self, limit=4):
        """Real scans that need a human decision: either a genuinely
        unrecognized fingerprint (id 0, database.py resolves this to the
        literal name 'Unregistered') or a recognized sensor ID with no
        matching student profile yet (resolved to 'Unknown ID:<n>')."""
        try:
            raw_records = get_attendance_today() or get_attendance_all() or []
        except Exception as e:
            self.log_message(f"Could not load today's attendance: {e}")
            raw_records = []

        abnormal = []
        for rec in raw_records:
            try:
                status = (rec.get("status") or "").lower()
                name = rec.get("student_name") or ""
                is_unresolved = name == "Unregistered" or name.startswith("Unknown ID:")
                if status == "unknown" or is_unresolved:
                    abnormal.append(rec)
            except Exception:
                continue
        abnormal.sort(key=lambda r: r.get("time", ""), reverse=True)
        return abnormal[:limit]

    def _build_abnormal_records_card(self, parent):
        ctk.CTkLabel(parent, text="Abnormal Attendance Record", text_color=WHS_TEXT_DARK,
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=18, pady=(14, 10))

        records = self._get_abnormal_records(limit=4)
        cards_row = ctk.CTkFrame(parent, fg_color="transparent")
        cards_row.pack(fill="both", expand=True, padx=14)

        if not records:
            ctk.CTkLabel(cards_row, text="✓ No unresolved scans right now.",
                         text_color=WHS_GREEN, font=("Segoe UI", 12)).pack(pady=30)
            return

        for i, rec in enumerate(records):
            fid = rec.get("fingerprint_id", 0)
            is_true_unknown = (fid == 0)

            card = ctk.CTkFrame(cards_row, fg_color="#f8f9fc", corner_radius=12,
                                 border_width=1, border_color="#eef0f5")
            card.pack(side="left", fill="both", expand=True, padx=6, pady=4)

            initials = "?" if is_true_unknown else str(fid)
            img = self._avatar(initials, i)
            if img is not None:
                ctk.CTkLabel(card, image=img, text="", fg_color="transparent").pack(pady=(14, 6))

            label = "Unknown Scan" if is_true_unknown else f"Fingerprint ID {fid}"
            ctk.CTkLabel(card, text=label, text_color=WHS_TEXT_DARK,
                         font=("Segoe UI", 12, "bold")).pack()
            ctk.CTkLabel(card, text=f"{rec.get('date', '')} {rec.get('time', '')}",
                         text_color=WHS_TEXT_GRAY, font=("Segoe UI", 10)).pack(pady=(0, 10))

            chip_text = "Needs Review" if is_true_unknown else "No Profile Linked"
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(anchor="w", padx=16, pady=2, fill="x")
            ctk.CTkLabel(row, text="\u26a0", text_color=WHS_ORANGE, font=("Segoe UI", 11)).pack(side="left")
            ctk.CTkLabel(row, text="  " + chip_text, text_color=WHS_ORANGE,
                         font=("Segoe UI", 10, "bold")).pack(side="left")

            if is_true_unknown:
                ctk.CTkButton(
                    card, text="Re-scan required", state="disabled",
                    fg_color=WHS_RED_LIGHT, text_color=WHS_RED, hover_color=WHS_RED_LIGHT,
                    corner_radius=16, height=34, font=("Segoe UI", 11, "bold")
                ).pack(pady=(10, 14), padx=16, fill="x")
            else:
                ctk.CTkButton(
                    card, text="➕  Assign to Student",
                    command=lambda f=fid: self.open_add_student_dialog(f),
                    fg_color=WHS_BLUE_LIGHT, text_color=WHS_BLUE, hover_color=WHS_BLUE_LIGHT,
                    corner_radius=16, height=34, font=("Segoe UI", 11, "bold")
                ).pack(pady=(10, 14), padx=16, fill="x")

    # ---- Need Work panel → repurposed as a real Quick Enroll assistant ----
    def _build_need_work_panel(self, parent):
        ctk.CTkLabel(parent, text="Need Work", text_color=WHS_TEXT_DARK,
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=18, pady=(12, 4))
        ctk.CTkLabel(
            parent, text="Enrollment requires a live sensor scan, so this panel\n"
                         "starts the real enroll flow — fields below are just notes.",
            text_color=WHS_TEXT_GRAY, font=("Segoe UI", 10), justify="left"
        ).pack(anchor="w", padx=18, pady=(0, 8))

        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=18)

        self.quick_enroll_name_var = ctk.StringVar()
        self.quick_enroll_section_var = ctk.StringVar()
        self.quick_enroll_notes_var = ctk.StringVar()

        fields = [
            ("\U0001F464", "Name", self.quick_enroll_name_var),
            ("\u26a0", "Section", self.quick_enroll_section_var),
        ]
        for icon, label, var in fields:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=f"{icon}  {label}", text_color=WHS_TEXT_GRAY, width=80, anchor="w",
                         font=("Segoe UI", 12)).pack(side="left")
            ctk.CTkEntry(row, textvariable=var, fg_color=WHS_BLUE_LIGHT, border_width=0,
                         corner_radius=8, height=26).pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(form, text="\U0001F4DD  Notes", text_color=WHS_TEXT_GRAY,
                     font=("Segoe UI", 12)).pack(anchor="w", pady=(6, 2))
        notes_box = ctk.CTkTextbox(form, fg_color=WHS_BLUE_LIGHT, corner_radius=8, height=60)
        notes_box.pack(fill="x")
        self.quick_enroll_notes_box = notes_box

        ctk.CTkButton(
            parent, text="➕  Start Enrollment", command=self._on_quick_enroll_submit,
            fg_color=WHS_BLUE, hover_color="#2c8ce0", corner_radius=18, height=36,
            font=("Segoe UI", 12, "bold")
        ).pack(padx=18, pady=(10, 14), fill="x")

    def _on_quick_enroll_submit(self):
        name = self.quick_enroll_name_var.get().strip()
        section = self.quick_enroll_section_var.get().strip()
        notes = self.quick_enroll_notes_box.get("1.0", "end").strip() if hasattr(self, "quick_enroll_notes_box") else ""
        if name:
            self.log_message(f"Quick enroll requested for '{name}' ({section}). Notes: {notes or '—'}")
        self.enroll_sample()

    # ---- System Status (real ESP32 / DB / last-scan state) ----------------
    def build_system_status_panel(self, parent):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=18, pady=14)

        ctk.CTkLabel(wrap, text="System Status", font=("Segoe UI", 14, "bold"),
                     text_color=WHS_TEXT_DARK).pack(anchor="w", pady=(0, 10))

        self.status_tab_esp_row = self._status_row(wrap, "ESP32 Connected", self.serial_handler.connected)
        self.status_tab_sensor_row = self._status_row(wrap, "Fingerprint Sensor Ready", self.serial_handler.connected)
        self.status_tab_db_row = self._status_row(wrap, "Database Connected", getattr(self, "db_ready", False))

        ctk.CTkFrame(wrap, fg_color="#eef0f5", height=1).pack(fill="x", pady=10)

        ctk.CTkLabel(wrap, text="Last Scan", text_color=WHS_TEXT_GRAY,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.status_tab_last_scan_label = ctk.CTkLabel(
            wrap, text="No scans yet", text_color=WHS_TEXT_DARK, font=("Segoe UI", 13, "bold")
        )
        self.status_tab_last_scan_label.pack(anchor="w", pady=(2, 10))

        info_card = ctk.CTkFrame(wrap, fg_color="#f8f9fc", corner_radius=10)
        info_card.pack(fill="x")
        self.status_tab_student_label = self._info_row(info_card, "Student", "—")
        self.status_tab_id_label = self._info_row(info_card, "ID", "—")
        self.status_tab_status_label = self._info_row(info_card, "Status", "—")

    def refresh_dashboard_tab(self):
        """Fully rebuilds the 🏠 Dashboard tab from live data."""
        if not hasattr(self, "tabview"):
            return
        try:
            tab = self.tabview.tab("🏠 Dashboard")
        except Exception:
            return
        for child in tab.winfo_children():
            child.destroy()
        self.build_dashboard_tab(tab)

    def _status_row(self, parent, label, ok):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)
        dot = ctk.CTkLabel(row, text="●", text_color=(COLOR_CONNECTED if ok else COLOR_DISCONNECTED),
                            font=("Segoe UI", 12))
        dot.pack(side="left")
        ctk.CTkLabel(row, text="  " + label, text_color=WHS_TEXT_DARK, font=("Segoe UI", 12)).pack(side="left")
        return dot

    def _info_row(self, parent, label, value):
        r = ctk.CTkFrame(parent, fg_color="transparent")
        r.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(r, text=label, text_color=WHS_TEXT_GRAY, font=("Segoe UI", 11)).pack(side="left")
        val = ctk.CTkLabel(r, text=value, text_color=WHS_TEXT_DARK, font=("Segoe UI", 11, "bold"))
        val.pack(side="right")
        return val

    # ------------------------------------------------------------------
    # WHS-style header bar (search / notifications / clock / live status)
    # ------------------------------------------------------------------
    def build_whs_header(self, main):
        bar = ctk.CTkFrame(main, corner_radius=14, height=56, fg_color=WHS_CARD_BG)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        bar.grid_propagate(False)

        # Left: logo badge + search box
        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left", padx=16, pady=10)

        ctk.CTkLabel(
            left, text="FP", fg_color=WHS_BLUE, text_color="white",
            corner_radius=10, width=40, height=30,
            font=("Segoe UI", 12, "bold")
        ).pack(side="left", padx=(0, 12))

        self.header_search_var = ctk.StringVar()
        search_box = ctk.CTkEntry(
            left, placeholder_text="🔍  Search students...",
            textvariable=self.header_search_var,
            fg_color=WHS_BLUE_LIGHT, border_width=0, corner_radius=10,
            width=200, height=32, font=("Segoe UI", 12)
        )
        search_box.pack(side="left")
        search_box.bind("<Return>", self._on_header_search)
        search_box.bind("<KeyRelease>", self._on_header_search)

        # Right: clock, live status pill, notification bell, power
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right", padx=16, pady=10)

        power_btn = ctk.CTkButton(
            right, text="⏻", width=32, height=32, corner_radius=16,
            fg_color=WHS_BLUE, hover_color="#2c8ce0", font=("Segoe UI", 13),
            command=self.quit_app
        )
        power_btn.pack(side="left", padx=(8, 0))

        bell = ctk.CTkButton(
            right, text="🔔", width=32, height=32, corner_radius=16,
            fg_color=WHS_BLUE_LIGHT, hover_color="#d8ecff",
            text_color=WHS_BLUE, font=("Segoe UI", 13),
            command=lambda: self.tabview.set("🖥 Live Log") if hasattr(self, "tabview") else None
        )
        bell.pack(side="left", padx=5)

        self.header_last_scan_label = ctk.CTkLabel(
            right, text="No scans yet", fg_color=WHS_BLUE_LIGHT,
            text_color=WHS_TEXT_GRAY, corner_radius=12,
            font=("Segoe UI", 11), padx=10, pady=4
        )
        self.header_last_scan_label.pack(side="left", padx=5)

        self.header_status_pill = ctk.CTkLabel(
            right, text="🔴  ESP32 Disconnected",
            fg_color=WHS_RED_LIGHT, text_color=COLOR_DISCONNECTED,
            corner_radius=12, font=("Segoe UI", 11, "bold"), padx=10, pady=4
        )
        self.header_status_pill.pack(side="left", padx=5)

        self.header_clock_label = ctk.CTkLabel(
            right, text="", corner_radius=12, fg_color=WHS_BLUE_LIGHT, text_color=WHS_TEXT_DARK,
            font=("Segoe UI", 11, "bold"), padx=10, pady=4
        )
        self.header_clock_label.pack(side="left", padx=5)
        self._tick_header_clock()

        # Reflect whatever the current connection state already is
        self._update_header_status(self.serial_handler.connected)

    def _tick_header_clock(self):
        if not self._ui_ready() or not hasattr(self, "header_clock_label"):
            return
        try:
            self.header_clock_label.configure(text=datetime.now().strftime("🕑  %I:%M:%S %p"))
        except Exception:
            pass
        self.after(1000, self._tick_header_clock)

    def _update_header_status(self, connected: bool):
        """Keep the header's ESP32 pill (and the System Status tab) in sync
        with the sidebar's status dot."""
        if hasattr(self, "header_status_pill"):
            if connected:
                self.header_status_pill.configure(
                    text="🟢  ESP32 Connected", fg_color=WHS_GREEN_LIGHT, text_color=COLOR_CONNECTED
                )
            else:
                self.header_status_pill.configure(
                    text="🔴  ESP32 Disconnected", fg_color=WHS_RED_LIGHT, text_color=COLOR_DISCONNECTED
                )
        for dot_attr in ("status_tab_esp_row", "status_tab_sensor_row"):
            dot = getattr(self, dot_attr, None)
            if dot is not None:
                try:
                    dot.configure(text_color=COLOR_CONNECTED if connected else COLOR_DISCONNECTED)
                except Exception:
                    pass

    def _update_header_last_scan(self, display: dict):
        """Show the most recent scan in the header pill AND the System
        Status tab — real data pulled straight from the attendance parser."""
        name = display.get("student_name") or "Unknown"
        when = display.get("time", "")
        if hasattr(self, "header_last_scan_label"):
            self.header_last_scan_label.configure(text=f"Last scan: {name} · {when}")
        if hasattr(self, "status_tab_last_scan_label"):
            self.status_tab_last_scan_label.configure(text=when or "—")
            self.status_tab_student_label.configure(text=name)
            self.status_tab_id_label.configure(text=str(display.get("fingerprint_id", "—")))
            self.status_tab_status_label.configure(text=display.get("status", "—"))

    def _on_header_search(self, event=None):
        """Live-filters the sidebar student roster as you type, and logs
        the query (Enter) for visibility in the Live Log tab."""
        self.refresh_student_roster()
        if event is not None and getattr(event, "keysym", None) == "Return":
            query = self.header_search_var.get().strip()
            if query:
                self.log_message(f"🔍 Searched students: '{query}'")


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
            self.stop_event.set()
            self.serial_handler.disconnect()
            self.status_var.set("Disconnected")
            self.status_dot.configure(text_color=COLOR_DISCONNECTED)
            self.connect_button.configure(text="Connect")
            self.scan_button.configure(state="disabled")
            self.stop_button.configure(state="disabled")
            self._update_header_status(False)
            self.log_message("Disconnected from ESP32.")
            return

        port = self.port_var.get().strip()
        if not port:
            self.log_message("Please choose a COM port before connecting.")
            self.log_message(build_serial_troubleshooting_message(self.serial_handler.list_available_ports()))
            return

        try:
            baud = int(self.baud_var.get())
        except Exception:
            baud = BAUD_RATE

        self.save_current_settings()

        ok, msg = self.serial_handler.connect(port, baud)
        if ok:
            self.status_var.set("Connected")
            self.status_dot.configure(text_color=COLOR_CONNECTED)
            self.connect_button.configure(text="Disconnect")
            self.scan_button.configure(state="normal")
            self._update_header_status(True)
            self.log_message(f"Connected to ESP32 on {port} at {baud} baud")
            self.start_reader_thread()
        else:
            self.status_var.set("Connection failed")
            self.status_dot.configure(text_color=COLOR_DISCONNECTED)
            self._update_header_status(False)
            self.log_message(f"Connection failed: {msg}")
            self.log_message(build_serial_troubleshooting_message(self.serial_handler.list_available_ports()))

    def _set_connected_ui(self):
        if getattr(self, '_closing', False):
            return
        self.status_var.set("Connected")
        self.status_dot.configure(text_color=COLOR_CONNECTED)
        self.connect_button.configure(text="Disconnect")
        self.scan_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self._update_header_status(True)

    def refresh_serial_ports(self, initial: bool = False):
        try:
            ports = self.serial_handler.list_available_ports() or []
            current_value = ""
            if hasattr(self, "port_var"):
                current_value = self.port_var.get().strip() if self.port_var.get() else ""

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
                baud = int(self.baud_var.get()) if getattr(self, "baud_var", None) and self.baud_var.get() else BAUD_RATE
                ok, msg = self.serial_handler.connect(port, baud)
                if ok:
                    self.status_var.set("Connected")
                    self.status_dot.configure(text_color=COLOR_CONNECTED)
                    self.connect_button.configure(text="Disconnect")
                    self.scan_button.configure(state="normal")
                    self.port_var.set(port)
                    self._update_header_status(True)
                    self.save_current_settings()
                    self.log_message(f"Auto-detected ESP32 on {port} at {baud} baud")
                    self.start_reader_thread()
                    if dialog is not None and dialog.winfo_exists():
                        dialog.destroy()
                    return True
            except Exception:
                continue
        self.log_message("No common COM port worked for the ESP32. Try the manual steps above.")
        return False

    def _set_disconnected_ui(self):
        if getattr(self, '_closing', False):
            return
        self.status_var.set("Disconnected")
        self.status_dot.configure(text_color=COLOR_DISCONNECTED)
        self.connect_button.configure(text="Connect")
        self.scan_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")
        self._update_header_status(False)

    def _set_reconnect_ui(self):
        if getattr(self, '_closing', False):
            return
        self.status_dot.configure(text_color=COLOR_DISCONNECTED)
        self.connect_button.configure(text="Disconnect")
        self.scan_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")
        self._update_header_status(False)

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

        if self.enroll_mode_active or self.wipe_mode_active:
            self.log_message("Cannot start scan while enrollment or wipe is active.")
            return

        if not self.serial_handler.connected:
            self.log_message("Please connect first.")
            return

        if cmd_scan(self.serial_handler):
            self._set_scan_mode_ui()
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

    def read_serial_output(self):
        last_reconnect_count = 0
        while not self.stop_event.is_set():
            line = self.serial_handler.read_line()
            if not self.serial_handler.connected:
                # Check if auto-reconnect is in progress
                if self.serial_handler.reconnect_count > 0:
                    if self.serial_handler.reconnect_count != last_reconnect_count:
                        last_reconnect_count = self.serial_handler.reconnect_count
                        status_text = f"Reconnecting... ({self.serial_handler.reconnect_count}/{RECONNECT_MAX_RETRIES})"
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

        student_count = len(get_all_students())
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
    def _parse_attendance(self, message):
        """Parse ESP32 output for attendance matches and auto-log them to database.
        
        Firmware outputs two lines per match:
          ID:1
          CONFIDENCE:223
        """
        from config import COOLDOWN_SECONDS
        
        # Look for "ID:N" pattern
        id_match = RE_ID_FOUND.search(message)
        if id_match:
            fingerprint_id = int(id_match.group(1))
            
            # Store detection info (next line will be CONFIDENCE if scan succeeded)
            self.__dict__['last_fingerprint_id'] = fingerprint_id
            self.__dict__['last_id_time'] = time.time()
            self.__dict__['last_confidence'] = 0  # Will be overwritten on next line
            return
        
        # Look for "CONFIDENCE:N" pattern — this completes the match
        confidence_match = RE_CONFIDENCE.search(message)
        last_fingerprint_id = self.__dict__.get('last_fingerprint_id')
        last_id_time = self.__dict__.get('last_id_time', 0)
        id_timeout = self.__dict__.get('ID_TIMEOUT', 2.0)
        if last_fingerprint_id is not None and (time.time() - last_id_time) > id_timeout:
            # Stale ID arrived without a confidence line; reset it before handling newer scans.
            self.__dict__['last_fingerprint_id'] = None
            self.__dict__['last_confidence'] = 0
            last_fingerprint_id = None

        if confidence_match and last_fingerprint_id is not None:
            fingerprint_id = last_fingerprint_id
            confidence = int(confidence_match.group(1))
            self.__dict__['last_confidence'] = confidence
            
            # Cooldown logic — track last *logged* separately from last *detected*
            # First scan logs immediately; subsequent scans of the same finger within COOLDOWN_SECONDS are blocked.
            last_logged_times = self.__dict__.get('last_logged_times')
            if last_logged_times is None:
                last_logged_times = {}
                self.__dict__['last_logged_times'] = last_logged_times
            current_time = time.time()
            last_logged_at = last_logged_times.get(fingerprint_id)
            if last_logged_at is None or (current_time - last_logged_at) > COOLDOWN_SECONDS:
                # Log to database regardless of whether a student profile exists.
                try:
                    student = get_student(fingerprint_id)
                    log_attendance(
                        fingerprint_id=fingerprint_id,
                        confidence=confidence,
                        status="Present"
                    )
                    if student:
                        self.log_message(f"✓ Attendance logged: {student.get('student_name', 'Unknown')} (ID {fingerprint_id}, confidence {confidence})")
                    else:
                        self.log_message(f"✓ Attendance logged for unknown fingerprint ID {fingerprint_id} (confidence {confidence})")
                    # Build a lightweight display dict and incrementally add the card to the UI
                    now = datetime.now()
                    rec = {
                        'fingerprint_id': fingerprint_id,
                        'student_no': student.get('student_no') if student else 'N/A',
                        'student_name': student.get('student_name') if student else None,
                        'grade': student.get('grade') if student else 'N/A',
                        'section': student.get('section') if student else 'N/A',
                        'date': now.strftime('%Y-%m-%d'),
                        'time': now.strftime('%H:%M:%S'),
                        'confidence': confidence,
                        'status': 'Present',
                        'has_student_profile': student is not None,
                    }
                    display = format_attendance_display(rec)
                    display['has_student_profile'] = student is not None
                    self.after(0, lambda d=display: self._update_header_last_scan(d))
                    self.after(200, self.refresh_dashboard_tab)
                    # Insert the new scan into the current view without rebuilding the entire list.
                    try:
                        today_str = datetime.now().strftime('%Y-%m-%d')
                        attendance_mode = getattr(self, 'attendance_mode', 'Today')
                        attendance_offset = getattr(self, 'attendance_offset', 0)

                        if self.tabview.get() == "📅 Attendance Log":
                            if attendance_mode == 'Today' and rec['date'] == today_str:
                                self.after(0, lambda d=display: build_attendance_card(self, d, prepend=True))
                                self._schedule_attendance_refresh()
                            elif attendance_mode == 'Recent' and attendance_offset == 0:
                                self.after(0, lambda d=display: build_attendance_card(self, d, prepend=True))
                                self._schedule_attendance_refresh()
                        # Otherwise skip incremental insert; user may refresh or load more.
                    except Exception:
                        self._schedule_attendance_refresh()
                    
                    # Update per-fingerprint cooldown tracking
                    last_logged_times[fingerprint_id] = current_time
                except Exception as e:
                    self.log_message(f"Error logging attendance: {e}")
            else:
                # Still within cooldown — silently skip (spam protection)
                pass
            
            # Reset detection state for next scan
            self.last_fingerprint_id = None
            return
        
        # Look for "UNKNOWN" — finger not recognized
        if RE_UNKNOWN.search(message):
            # Rate-limit UNKNOWN logging using a separate global throttle
            # (not per-fingerprint, since all unknowns share the same ID 0)
            try:
                current_time = time.time()
                last_unknown_time = self.__dict__.get('last_unknown_time', None)
                if last_unknown_time is None or (current_time - last_unknown_time) > COOLDOWN_SECONDS:
                    now = datetime.now()
                    log_attendance(0, 0, "UNKNOWN", now)
                    self.log_message(f"⚠ Unknown fingerprint scanned — saved to attendance log ({now.strftime('%Y-%m-%d %H:%M:%S')})")
                    # Refresh the current attendance view to show the new unknown scan
                    rec = {
                        'fingerprint_id': 0,
                        'student_no': 'N/A',
                        'student_name': None,
                        'grade': 'N/A',
                        'section': 'N/A',
                        'date': now.strftime('%Y-%m-%d'),
                        'time': now.strftime('%H:%M:%S'),
                        'confidence': 0,
                        'status': 'UNKNOWN',
                    }
                    display = format_attendance_display(rec)
                    self.after(0, lambda d=display: self._update_header_last_scan(d))
                    self.after(200, self.refresh_dashboard_tab)
                    try:
                        today_str = datetime.now().strftime('%Y-%m-%d')
                        attendance_mode = getattr(self, 'attendance_mode', 'Today')
                        attendance_offset = getattr(self, 'attendance_offset', 0)

                        if self.tabview.get() == "📅 Attendance Log":
                            if attendance_mode == 'Today' and rec['date'] == today_str:
                                self.after(0, lambda d=display: build_attendance_card(self, d, prepend=True))
                                self._schedule_attendance_refresh()
                            elif attendance_mode == 'Recent' and attendance_offset == 0:
                                self.after(0, lambda d=display: build_attendance_card(self, d, prepend=True))
                                self._schedule_attendance_refresh()
                    except Exception:
                        self._schedule_attendance_refresh()
                    # Update the global unknown throttle time
                    self.__dict__['last_unknown_time'] = current_time
                else:
                    # Skipped due to cooldown
                    pass
            except Exception as e:
                self.log_message(f"Error saving unknown scan: {e}")
            finally:
                self.last_fingerprint_id = None

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
        result = self.students_page.refresh()
        self.refresh_student_roster()
        return result

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


    def _build_attendance_card(self, display: dict, prepend: bool = True):
        return build_attendance_card(self, display, prepend)

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
            self._parse_attendance(raw_message)
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