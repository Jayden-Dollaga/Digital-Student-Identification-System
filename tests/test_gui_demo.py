"""
Test GUI for Fingerprint Attendance System
Enhanced version with professional design and realistic data.
"""
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
python_dir = PYTHON_ROOT / "python"
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))

import customtkinter as ctk
from datetime import datetime, timedelta
import json

from settings_store import load_settings, save_settings
from gui.theme import get_theme_colors, apply_appearance_mode


class AttendanceTestGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Fingerprint Attendance System - Professional Test GUI")
        self.geometry("1400x900")
        self.minsize(1000, 700)
        
        # Apply dark theme
        ctk.set_appearance_mode("dark")
        
        self.settings = load_settings()
        self.current_role = "Administrator"
        self.current_user = "Admin User"
        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main background
        main_bg = ctk.CTkFrame(self)
        main_bg.grid(row=0, column=0, columnspan=2, sticky="nsew")
        
        self.build_sidebar()
        self.build_top_bar()
        self.build_main_content()
        self.log_message("Professional Test GUI initialized. Toggle settings to test!")
    
    def build_sidebar(self):
        """Build a professional left sidebar with navigation and settings."""
        sidebar = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color="#1a1a1a")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        
        # Logo/Brand
        brand_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand_frame.pack(anchor="w", padx=16, pady=16)
        
        ctk.CTkLabel(brand_frame, text="📊 WHS", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(brand_frame, text="Attendance System", font=("Segoe UI", 9), text_color="#8b8c8d").pack(anchor="w")
        
        # User info
        user_frame = ctk.CTkFrame(sidebar, fg_color="#2a2a2a", corner_radius=8)
        user_frame.pack(fill="x", padx=12, pady=12)
        
        ctk.CTkLabel(user_frame, text=self.current_user, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(user_frame, text=self.current_role, font=("Segoe UI", 9), text_color="#8b8c8d").pack(anchor="w", padx=12, pady=(0, 8))
        
        # Settings section
        settings_label = ctk.CTkLabel(sidebar, text="⚙ Settings", font=("Segoe UI", 10, "bold"), text_color="#8b8c8d")
        settings_label.pack(anchor="w", padx=16, pady=(16, 8))
        
        settings_frame = ctk.CTkFrame(sidebar, fg_color="#2a2a2a", corner_radius=8)
        settings_frame.pack(fill="x", padx=12, pady=(0, 12))
        settings_frame.grid_columnconfigure(0, weight=1)
        
        # Auto Reconnect
        self.auto_reconnect_var = ctk.BooleanVar(value=self.settings.get("auto_reconnect", True))
        ctk.CTkCheckBox(
            settings_frame,
            text="Auto-Reconnect",
            variable=self.auto_reconnect_var,
            command=self.on_setting_changed,
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=12, pady=6)
        
        # Auto Detect Serial
        self.auto_detect_var = ctk.BooleanVar(value=self.settings.get("auto_detect_serial", True))
        ctk.CTkCheckBox(
            settings_frame,
            text="Auto-Detect ESP32",
            variable=self.auto_detect_var,
            command=self.on_setting_changed,
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=12, pady=6)
        
        # Compact Sidebar
        self.compact_var = ctk.BooleanVar(value=self.settings.get("compact_sidebar", False))
        ctk.CTkCheckBox(
            settings_frame,
            text="Compact Sidebar",
            variable=self.compact_var,
            command=self.on_setting_changed,
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=12, pady=6)
        
        # Enable Profiler
        self.profiler_var = ctk.BooleanVar(value=self.settings.get("enable_profiler", False))
        ctk.CTkCheckBox(
            settings_frame,
            text="Enable Profiler",
            variable=self.profiler_var,
            command=self.on_setting_changed,
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=12, pady=6)
        
        # Save button
        ctk.CTkButton(
            settings_frame,
            text="💾 Save Settings",
            command=self.save_settings,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            height=36,
            corner_radius=6,
            font=("Segoe UI", 10, "bold")
        ).pack(fill="x", padx=12, pady=(12, 12))
        
        # Status section
        status_label = ctk.CTkLabel(sidebar, text="Status", font=("Segoe UI", 10, "bold"), text_color="#8b8c8d")
        status_label.pack(anchor="w", padx=16, pady=(16, 8))
        
        status_frame = ctk.CTkFrame(sidebar, fg_color="#2a2a2a", corner_radius=8)
        status_frame.pack(fill="x", padx=12, pady=(0, 12))
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="✓ Ready",
            text_color="#2ecc71",
            font=("Segoe UI", 10, "bold")
        )
        self.status_label.pack(anchor="w", padx=12, pady=8)
        
        # Log section
        log_label = ctk.CTkLabel(sidebar, text="Log", font=("Segoe UI", 10, "bold"), text_color="#8b8c8d")
        log_label.pack(anchor="w", padx=16, pady=(8, 4))
        
        log_frame = ctk.CTkFrame(sidebar, fg_color="#1f1f1f", corner_radius=6)
        log_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        self.log_text = ctk.CTkTextbox(log_frame, state="disabled", text_color="#8b8c8d")
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        
        self.sidebar = sidebar
    
    def build_top_bar(self):
        """Build the top navigation bar."""
        top_bar = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color="#1f1f1f")
        top_bar.grid(row=0, column=1, sticky="new", padx=16, pady=(12, 0))
        top_bar.grid_propagate(False)
        top_bar.grid_columnconfigure(1, weight=1)
        
        # Title
        ctk.CTkLabel(
            top_bar,
            text="📊 Work Attendance",
            font=("Segoe UI", 16, "bold")
        ).grid(row=0, column=0, sticky="w", padx=(0, 16))
        
        # Date
        date_str = datetime.now().strftime("%b %d, %Y")
        ctk.CTkLabel(
            top_bar,
            text=f"📅 {date_str}",
            font=("Segoe UI", 10),
            text_color="#8b8c8d"
        ).grid(row=0, column=1, sticky="e")
    
    def build_main_content(self):
        """Build the main content area with attendance records."""
        main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main.grid(row=1, column=1, sticky="nsew", padx=16, pady=(8, 16))
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)
        
        # Attendance table section
        table_frame = ctk.CTkFrame(main, corner_radius=10, fg_color="#2a2a2a")
        table_frame.grid(row=0, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(1, weight=1)
        
        # Title
        ctk.CTkLabel(
            table_frame,
            text="📋 Attendance Records - Weekly Overview",
            font=("Segoe UI", 12, "bold")
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 8))
        
        # Scrollable content - no extra padding
        scroll_frame = ctk.CTkScrollableFrame(table_frame, fg_color="transparent")
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)
        scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Attendance data - FULL LIST
        attendance_data = [
            ("Employee Name", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
            ("John Doe", "✓", "✓", "✓", "✓", "✓", "-", "-"),
            ("Jane Smith", "✓", "✓", "✓", "✓", "✓", "-", "-"),
            ("Mike Johnson", "✓", "✓", "✗", "✓", "✓", "-", "-"),
            ("Sarah Williams", "✓", "✓", "✓", "✓", "✓", "-", "-"),
            ("Alex Brown", "✓", "✗", "✓", "✓", "✓", "-", "-"),
            ("Emily Davis", "✓", "✓", "✓", "✗", "✓", "-", "-"),
            ("Chris Lee", "✓", "✓", "✓", "✓", "✓", "-", "-"),
            ("Jessica Brown", "✓", "✓", "✗", "✓", "✗", "-", "-"),
            ("David Martinez", "✓", "✓", "✓", "✓", "✓", "-", "-"),
            ("Angela Garcia", "✗", "✓", "✓", "✓", "✓", "-", "-"),
            ("Robert Taylor", "✓", "✓", "✓", "✓", "✓", "-", "-"),
            ("Maria Anderson", "✓", "✓", "✓", "✗", "✓", "-", "-"),
            ("James Wilson", "✓", "✓", "✓", "✓", "✓", "-", "-"),
            ("Lisa Thomas", "✓", "✓", "✓", "✓", "✓", "-", "-"),
            ("Richard Jackson", "✓", "✗", "✓", "✓", "✓", "-", "-"),
        ]
        
        for i, row in enumerate(attendance_data):
            # Header row styling
            if i == 0:
                row_frame = ctk.CTkFrame(scroll_frame, fg_color="#1f1f1f", corner_radius=6)
                font = ("Segoe UI", 10, "bold")
                text_color = "#64748b"
            else:
                # Alternate colors for better readability
                if i % 2 == 0:
                    row_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                else:
                    row_frame = ctk.CTkFrame(scroll_frame, fg_color="#252525", corner_radius=4)
                font = ("Segoe UI", 9)
                text_color = "white"
            
            row_frame.grid(row=i, column=0, sticky="ew", pady=2)
            row_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)
            
            for j, cell in enumerate(row):
                cell_label = ctk.CTkLabel(
                    row_frame,
                    text=cell,
                    font=font,
                    text_color=text_color
                )
                cell_label.grid(row=0, column=j, padx=6, pady=4, sticky="ew")
        
        self.main_content = main
    
    def on_setting_changed(self):
        """Called when any setting toggle changes."""
        active_count = sum([
            self.auto_reconnect_var.get(),
            self.auto_detect_var.get(),
            self.compact_var.get(),
            self.profiler_var.get(),
        ])
        self.log_message(f"⚙ Toggle changed - {active_count}/4 active")
    
    def save_settings(self):
        """Save the current toggle settings."""
        new_settings = self.settings.copy()
        new_settings.update({
            "auto_reconnect": self.auto_reconnect_var.get(),
            "auto_detect_serial": self.auto_detect_var.get(),
            "compact_sidebar": self.compact_var.get(),
            "enable_profiler": self.profiler_var.get(),
        })
        
        save_settings(new_settings)
        self.settings = new_settings
        
        self.status_label.configure(text="✓ Saved successfully")
        self.log_message("✓ Settings saved successfully!")
        self.after(2000, lambda: self.status_label.configure(text="✓ Ready"))
    
    def log_message(self, msg: str):
        """Add a message to the log area."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")


if __name__ == "__main__":
    app = AttendanceTestGUI()
    app.mainloop()
