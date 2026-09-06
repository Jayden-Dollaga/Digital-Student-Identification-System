import customtkinter as ctk
from tkinter import messagebox

from config import get_config
from core.firmware_helper import discover_firmware_candidates, find_firmware_binary, upload_firmware
from settings_store import save_settings

CONFIG = get_config()
from gui.theme import apply_appearance_mode


def open_settings_dialog(app):
    """Open the runtime settings dialog for the main GUI."""
    if hasattr(app, "settings_dialog") and app.settings_dialog is not None and app.settings_dialog.winfo_exists():
        app.settings_dialog.lift()
        app.settings_dialog.focus()
        return

    dialog = ctk.CTkToplevel(app)
    dialog.title("Application Settings")
    # use responsive dialog sizing so it fits small screens
    screen_width = app.winfo_screenwidth() if app.winfo_screenwidth() > 0 else 1440
    screen_height = app.winfo_screenheight() if app.winfo_screenheight() > 0 else 900
    try:
        from gui.layout_utils import resolve_dialog_size
        w, h = resolve_dialog_size(screen_width, screen_height, 480, 420)
        dialog.geometry(f"{w}x{h}")
    except Exception:
        dialog.geometry("420x420")
    dialog.transient(app)
    dialog.grab_set()
    dialog.grid_columnconfigure(0, weight=1)
    dialog.grid_rowconfigure(0, weight=1)

    content = ctk.CTkFrame(dialog, corner_radius=10)
    content.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
    content.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(content, text="Settings", font=("Segoe UI", 16, "bold")).grid(
        row=0, column=0, sticky="w", pady=(0, 12)
    )

    ctk.CTkLabel(content, text="COM Port", font=("Segoe UI", 11)).grid(
        row=1, column=0, sticky="w", pady=(4, 2)
    )
    port_menu = ctk.CTkComboBox(
        content,
        values=app.serial_handler.list_available_ports() or [app.port_var.get()],
        variable=app.port_var,
        state="normal"
    )
    port_menu.grid(row=2, column=0, sticky="ew", pady=(0, 8))

    refresh_ports_button = ctk.CTkButton(
        content,
        text="Refresh Ports",
        width=120,
        command=lambda: _refresh_ports(port_menu, app)
    )
    refresh_ports_button.grid(row=3, column=0, sticky="w", pady=(0, 12))

    ctk.CTkLabel(content, text="Baud Rate", font=("Segoe UI", 11)).grid(
        row=4, column=0, sticky="w", pady=(4, 2)
    )
    baud_menu = ctk.CTkComboBox(
        content,
        values=[str(rate) for rate in CONFIG.baud_rates],
        variable=app.baud_var,
        state="readonly"
    )
    baud_menu.grid(row=5, column=0, sticky="ew", pady=(0, 8))

    ctk.CTkLabel(content, text="Theme Mode", font=("Segoe UI", 11)).grid(
        row=6, column=0, sticky="w", pady=(4, 2)
    )
    theme_var = ctk.StringVar(value=app.settings.get("theme", "dark"))
    theme_menu = ctk.CTkOptionMenu(
        content,
        values=list(CONFIG.theme_modes),
        variable=theme_var,
        command=None
    )
    theme_menu.grid(row=7, column=0, sticky="ew", pady=(0, 8))

    firmware_status_var = ctk.StringVar(value="")
    ctk.CTkLabel(content, text="ESP32 Firmware Helper", font=("Segoe UI", 11, "bold")).grid(
        row=8, column=0, sticky="w", pady=(8, 2)
    )
    firmware_help = ctk.CTkLabel(
        content,
        text="Use this helper to locate bundled firmware or try a simple esptool upload using the selected COM port.",
        wraplength=520,
        justify="left",
        text_color=("gray20", "gray80"),
    )
    firmware_help.grid(row=9, column=0, sticky="w", pady=(0, 6))

    firmware_progress_var = ctk.StringVar(value="")

    def _refresh_firmware_status():
        candidates = discover_firmware_candidates()
        binary = find_firmware_binary()
        if binary is not None:
            firmware_status_var.set(f"Firmware ready: {binary.name}")
            firmware_progress_var.set("")
            upload_btn.configure(state="normal")
        elif candidates:
            firmware_status_var.set(f"Firmware source found: {candidates[0].name}")
            firmware_progress_var.set("")
            upload_btn.configure(state="disabled")
        else:
            firmware_status_var.set("No bundled firmware detected.")
            firmware_progress_var.set("")
            upload_btn.configure(state="disabled")

    _refresh_firmware_status()
    ctk.CTkLabel(content, textvariable=firmware_status_var, wraplength=520, justify="left").grid(
        row=10, column=0, sticky="w", pady=(0, 8)
    )

    firmware_buttons = ctk.CTkFrame(content, fg_color="transparent")
    firmware_buttons.grid(row=11, column=0, sticky="ew", pady=(0, 10))
    firmware_buttons.grid_columnconfigure(0, weight=1)
    firmware_buttons.grid_columnconfigure(1, weight=1)

    def _upload_firmware():
        port = app.port_var.get().strip() if getattr(app, "port_var", None) else ""
        if not port:
            messagebox.showwarning("Firmware Upload", "Select a COM port first.", parent=dialog)
            return

        upload_btn.configure(state="disabled")
        firmware_progress_var.set("Starting upload...")

        def _progress(line: str):
            firmware_progress_var.set(line)

        def _run_upload():
            ok, msg = upload_firmware_with_progress(port=port, progress_callback=_progress)
            if ok:
                messagebox.showinfo("Firmware Upload", "Upload successful.", parent=dialog)
            else:
                messagebox.showerror("Firmware Upload", f"Upload failed: {msg}", parent=dialog)
            upload_btn.configure(state="normal")

        # Launch upload in background so UI stays responsive
        import threading

        threading.Thread(target=_run_upload, daemon=True).start()

    upload_btn = ctk.CTkButton(
        firmware_buttons,
        text="Upload Firmware",
        command=_upload_firmware,
        height=36,
        corner_radius=8,
    )
    upload_btn.grid(row=0, column=1, sticky="ew")

    ctk.CTkButton(
        firmware_buttons,
        text="Refresh Firmware Info",
        command=_refresh_firmware_status,
        height=36,
        corner_radius=8,
    ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

    # Show a short status line and allow wrapping for longer esptool progress
    ctk.CTkLabel(content, textvariable=firmware_progress_var, wraplength=520, justify="left").grid(
        row=12, column=0, sticky="w", pady=(6, 8)
    )

    auto_reconnect_var = ctk.BooleanVar(value=app.serial_handler.auto_reconnect_enabled)
    auto_detect_var = ctk.BooleanVar(value=app.settings.get("auto_detect_serial", True))
    compact_sidebar_var = ctk.BooleanVar(value=app.settings.get("compact_sidebar", False))
    enable_profiler_var = ctk.BooleanVar(value=app.settings.get("enable_profiler", False))
    ctk.CTkCheckBox(
        content,
        text="Enable Auto-Reconnect",
        variable=auto_reconnect_var
    ).grid(row=12, column=0, sticky="w", pady=(4, 2))
    ctk.CTkCheckBox(
        content,
        text="Auto-detect ESP32 on refresh/startup",
        variable=auto_detect_var
    ).grid(row=13, column=0, sticky="w", pady=(0, 12))

    ctk.CTkLabel(
        content,
        text="Screen scaling is no longer available. The UI now uses a fixed layout for more reliable behavior.",
        wraplength=520,
        text_color=("gray20", "gray80"),
    ).grid(row=14, column=0, sticky="w", pady=(0, 12))

    ctk.CTkCheckBox(
        content,
        text="Compact sidebar (icons-only)",
        variable=compact_sidebar_var
    ).grid(row=15, column=0, sticky="w", pady=(0, 12))

    ctk.CTkCheckBox(
        content,
        text="Enable lightweight UI profiler",
        variable=enable_profiler_var
    ).grid(row=16, column=0, sticky="w", pady=(0, 12))

    button_row = ctk.CTkFrame(content, fg_color="transparent")
    button_row.grid(row=17, column=0, sticky="ew", pady=(16, 0))
    button_row.grid_columnconfigure(0, weight=1)
    button_row.grid_columnconfigure(1, weight=1)

    def _save_settings():
        try:
            app.serial_handler.auto_reconnect_enabled = auto_reconnect_var.get()
            if theme_var.get():
                apply_appearance_mode("Dark" if theme_var.get().lower() == "dark" else "Light", app)
            app.settings = {
                "com_port": app.port_var.get().strip() if getattr(app, "port_var", None) else "",
                "baud_rate": int(app.baud_var.get()) if getattr(app, "baud_var", None) else 115200,
                "cooldown": app.settings.get("cooldown", 10),
                "theme": theme_var.get().lower(),
                "auto_reconnect": auto_reconnect_var.get(),
                "auto_detect_serial": auto_detect_var.get(),
                "compact_sidebar": compact_sidebar_var.get(),
                "enable_profiler": enable_profiler_var.get(),
            }
            save_settings(app.settings)
            app.serial_handler.auto_reconnect_enabled = auto_reconnect_var.get()
            app.auto_detect_serial = auto_detect_var.get()
            app.profiler.enabled = enable_profiler_var.get()
            if getattr(app, "sidebar", None) is not None:
                app.sidebar.destroy()
                app.sidebar = app.build_sidebar()
            app.log_message("Settings updated.")
            dialog.destroy()
        except Exception as err:
            messagebox.showerror("Settings Error", f"Could not save settings: {err}", parent=dialog)

    ctk.CTkButton(
        button_row,
        text="Save",
        command=_save_settings,
        height=40,
        corner_radius=8,
    ).grid(row=0, column=0, padx=(0, 8), sticky="ew")
    ctk.CTkButton(
        button_row,
        text="Close",
        fg_color="transparent",
        border_width=1,
        command=dialog.destroy,
        height=40,
        corner_radius=8,
    ).grid(row=0, column=1, sticky="ew")

    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    app.settings_dialog = dialog


def _refresh_ports(port_menu, app):
    ports = app.serial_handler.list_available_ports() or []
    if ports:
        port_menu.configure(values=ports)
        app.port_var.set(ports[0])
    else:
        port_menu.configure(values=[app.port_var.get()])
    app.log_message("Serial port list refreshed.")
