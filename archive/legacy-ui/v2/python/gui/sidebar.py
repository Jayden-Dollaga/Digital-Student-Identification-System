import customtkinter as ctk

from config import get_config, get_default_com_port
from settings_store import load_settings

CONFIG = get_config()
from gui.theme import get_theme_colors
from gui.layout_utils import resolve_sidebar_width, scale_value


def build_sidebar(app):
    colors = get_theme_colors(ctk.get_appearance_mode())
    screen_width = app.winfo_screenwidth() if app.winfo_screenwidth() > 0 else 1440
    screen_height = app.winfo_screenheight() if app.winfo_screenheight() > 0 else 900
    scaling_factor = getattr(app, "scaling_factor", 1.0)
    sidebar_width = resolve_sidebar_width(screen_width, screen_height)
    # Allow the sidebar to shrink on narrow screens; avoid forcing fixed propagation
    sidebar = ctk.CTkFrame(app, width=sidebar_width, corner_radius=0)
    sidebar.grid(row=0, column=0, sticky="nsw")
    try:
        sidebar.grid_propagate(True)
    except Exception:
        pass
    sidebar.grid_columnconfigure(0, weight=1)

    # Use a scrollable frame for sidebar contents so controls never get cut off
    # Ensure the scrollable area expands so controls are reachable on small screens
    scroll = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
    scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
    sidebar.grid_rowconfigure(0, weight=1)
    # ensure scrollable area allows its single column to expand so child frames fill width
    scroll.grid_columnconfigure(0, weight=1)

    # --- App header ---
    header = ctk.CTkFrame(scroll, fg_color="transparent")
    header.grid(row=0, column=0, padx=max(10, int(16 * scaling_factor)), pady=(max(12, int(20 * scaling_factor)), max(8, int(10 * scaling_factor))), sticky="ew")
    ctk.CTkLabel(header, text="🖐️  Fingerprint", font=("Segoe UI", 16, "bold")).pack(anchor="w")
    ctk.CTkLabel(header, text="Attendance System", font=("Segoe UI", 12), text_color=colors["muted_text"]).pack(anchor="w")

    # --- Connection card ---
    connection_card = ctk.CTkFrame(scroll, corner_radius=10)
    connection_card.grid(row=1, column=0, padx=max(10, int(16 * scaling_factor)), pady=(max(8, int(10 * scaling_factor)), max(8, int(12 * scaling_factor))), sticky="ew")
    connection_card.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(connection_card, text="ESP32 Connection", font=("Segoe UI", 13, "bold")).grid(
        row=0, column=0, padx=12, pady=(12, 8), sticky="w"
    )

    saved_settings = load_settings()
    initial_port = saved_settings.get("com_port") or get_default_com_port(CONFIG.com_port)
    app.port_var = ctk.StringVar(value=initial_port)
    app.baud_var = ctk.StringVar(value=str(saved_settings.get("baud_rate", CONFIG.baud_rate)))

    port_row = ctk.CTkFrame(connection_card, fg_color="transparent")
    port_row.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
    port_row.grid_columnconfigure(0, weight=1)

    app.port_combobox = ctk.CTkComboBox(
        port_row,
        values=app.serial_handler.list_available_ports() or [initial_port],
        variable=app.port_var,
        state="normal"
    )
    app.port_combobox.grid(row=0, column=0, sticky="ew")

    ctk.CTkButton(port_row, text="Refresh", width=90, command=app.refresh_serial_ports).grid(
        row=0, column=1, padx=(8, 0)
    )

    ctk.CTkLabel(connection_card, text="Baud Rate", font=("Segoe UI", 11), text_color=colors["muted_text"]).grid(
        row=2, column=0, padx=12, pady=(0, 0), sticky="w"
    )
    app.baud_combobox = ctk.CTkComboBox(
        connection_card,
        values=[str(rate) for rate in CONFIG.baud_rates],
        variable=app.baud_var,
        state="readonly"
    )
    app.baud_combobox.grid(row=3, column=0, padx=12, pady=(0, 8), sticky="ew")

    app.connect_button = ctk.CTkButton(
        connection_card,
        text="Connect",
        command=app.toggle_connection,
        fg_color="#3b82f6",
        height=max(36, int(42 * scaling_factor)),
        corner_radius=8,
        font=("Segoe UI", 12, "bold"),
    )
    app.connect_button.grid(row=4, column=0, padx=12, pady=(0, 8), sticky="ew")

    status_row = ctk.CTkFrame(connection_card, fg_color="transparent")
    status_row.grid(row=5, column=0, padx=12, pady=(0, 12), sticky="ew")
    app.status_dot = ctk.CTkLabel(status_row, text="●", text_color="#e74c3c", font=("Segoe UI", 14))
    app.status_dot.pack(side="left")
    app.status_var = ctk.StringVar(value="Disconnected")
    ctk.CTkLabel(status_row, textvariable=app.status_var, text_color=colors["muted_text"]).pack(side="left", padx=(6, 0))

    # --- Quick actions card ---
    actions_card = ctk.CTkFrame(scroll, corner_radius=10)
    actions_card.grid(row=2, column=0, padx=max(10, int(16 * scaling_factor)), pady=(0, max(8, int(12 * scaling_factor))), sticky="ew")
    actions_card.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(actions_card, text="Quick Actions", font=("Segoe UI", 13, "bold")).grid(
        row=0, column=0, padx=12, pady=(12, 8), sticky="w"
    )

    button_stack = ctk.CTkFrame(actions_card, fg_color="transparent")
    button_stack.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="ew")
    button_stack.grid_columnconfigure(0, weight=1)
    compact = bool(getattr(app, "settings", {}).get("compact_sidebar", False))

    def _add_action_button(text, command, **kwargs):
        # In compact mode show only the leading icon/token and reduce size
        if compact:
            display_text = text.split()[0] if text and len(text.split()) > 0 else text
            btn_height = max(28, int(32 * scaling_factor))
            btn_font = ("Segoe UI", 10)
        else:
            display_text = text
            btn_height = max(34, int(40 * scaling_factor))
            btn_font = ("Segoe UI", 12)

        btn = ctk.CTkButton(
            button_stack,
            text=display_text,
            command=command,
            height=btn_height,
            corner_radius=8,
            font=btn_font,
            **kwargs,
        )
        return btn

    app.scan_button = _add_action_button("▶  Start Scan", app.start_scan, state="disabled")
    app.scan_button.grid(row=0, column=0, pady=4, sticky="ew")

    app.stop_button = _add_action_button(
        "⏹  Stop Scan",
        app.stop_scan,
        state="disabled",
        fg_color="transparent",
        border_width=1,
    )
    app.stop_button.grid(row=1, column=0, pady=4, sticky="ew")

    app.enroll_button = _add_action_button("➕ Enroll", app.enroll_sample)
    app.enroll_button.grid(row=2, column=0, pady=(10, 4), sticky="ew")

    app.list_button = _add_action_button(
        "📋 List",
        app.list_fingerprints,
        fg_color="transparent",
        border_width=1,
    )
    app.list_button.grid(row=3, column=0, pady=4, sticky="ew")

    app.wipe_button = _add_action_button(
        "⚠ Wipe",
        app.open_wipe_dialog,
        fg_color="#e74c3c",
        hover_color="#c0392b",
    )
    app.wipe_button.grid(row=4, column=0, pady=4, sticky="ew")

    app.backup_button = _add_action_button(
        "💾 Backup DB",
        app.backup_database,
        fg_color="#16a34a",
        hover_color="#15803d",
    )
    app.backup_button.grid(row=5, column=0, pady=4, sticky="ew")

    app.restore_button = _add_action_button(
        "🔁 Restore DB",
        app.open_restore_dialog,
        fg_color="#f59e0b",
        hover_color="#d97706",
    )
    app.restore_button.grid(row=6, column=0, pady=4, sticky="ew")

    app.settings_button = _add_action_button(
        "⚙ Settings",
        app.open_settings_dialog,
        fg_color="#6366f1",
        hover_color="#4f46e5",
    )
    app.settings_button.grid(row=7, column=0, pady=4, sticky="ew")

    app.help_serial_button = _add_action_button(
        "🛠 Help Connect ESP32",
        app.show_serial_help,
        fg_color="#0f766e",
        hover_color="#115e59",
    )
    app.help_serial_button.grid(row=8, column=0, pady=4, sticky="ew")

    app.quit_button = _add_action_button(
        "Quit",
        app.quit_app,
        fg_color="transparent",
        border_width=1,
        text_color=("gray10", "gray90"),
    )
    app.quit_button.grid(row=9, column=0, pady=(10, 0), sticky="ew")

    # Runtime adaptive resizing removed to avoid flicker and excessive UI work

    app.update_button_permissions()

    # Version label stays pinned at the bottom of the sidebar (outside the scrollable area)
    ctk.CTkLabel(
        sidebar, text="v2.0  ·  ESP32 + Fingerprint Sensor",
        font=("Segoe UI", 10), text_color=colors["muted_text"]
    ).grid(row=1, column=0, padx=max(10, int(16 * scaling_factor)), pady=(0, max(10, int(16 * scaling_factor))), sticky="sw")
