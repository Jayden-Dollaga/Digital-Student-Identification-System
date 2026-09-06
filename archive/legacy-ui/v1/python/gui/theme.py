"""Color and theme helpers for the compatibility CustomTkinter UI."""

import customtkinter as ctk

# Centralized theme helpers


THEME_COLORS = {
    "dark": {
        "muted_text": "#8b8c8d",
        "card_background": "#2a2a2a",
        "surface_background": "#1f1f1f",
        "subtle_border": "#3a3a3a",
    },
    "light": {
        "muted_text": "#64748b",
        "card_background": "#f8fafc",
        "surface_background": "#f8fafc",
        "subtle_border": "#e2e8f0",
    },
}


def _normalize_mode(mode):
    if not mode:
        return "dark"
    value = str(mode).strip().lower()
    if value in {"light", "dark", "system"}:
        return value
    if value in {"lightmode", "light mode"}:
        return "light"
    if value in {"darkmode", "dark mode"}:
        return "dark"
    return "dark"


def _apply_widget_theme(widget, colors):
    try:
        widget_class = widget.__class__.__name__
        if widget_class in {"CTkFrame", "CTkScrollableFrame"}:
            current_fg = widget.cget("fg_color")
            if current_fg in {"#2a2a2a", "#1f1f1f", "#1e1e1e", "#2f2f2f", "#222222", "#111111", "#3b3b3b"}:
                widget.configure(fg_color=colors["card_background"])
        elif widget_class == "CTkLabel":
            current_text = widget.cget("text_color")
            if current_text in {"#8b8c8d", "#8b8b8d", "#8b8b8b", "#f8fafc", "#e5e7eb"}:
                widget.configure(text_color=colors["muted_text"])
    except Exception:
        pass

    try:
        for child in widget.winfo_children():
            _apply_widget_theme(child, colors)
    except Exception:
        pass


def refresh_widget_theme_tree(root, mode=None):
    colors = get_theme_colors(mode)
    if root is None:
        return
    try:
        _apply_widget_theme(root, colors)
    except Exception:
        pass


def apply_appearance_mode(mode, app=None):
    normalized = _normalize_mode(mode)

    def _apply_once():
        try:
            if app is not None and hasattr(app, "winfo_exists") and not app.winfo_exists():
                return
            if app is not None and hasattr(app, "update_idletasks"):
                try:
                    app.update_idletasks()
                except Exception:
                    pass
            ctk.set_appearance_mode(normalized)
            if app is not None:
                try:
                    refresh_widget_theme_tree(app, normalized)
                except Exception:
                    pass
        except Exception:
            pass

    if app is not None and hasattr(app, "after"):
        try:
            app.after(25, _apply_once)
        except Exception:
            _apply_once()
    else:
        _apply_once()


def get_theme_colors(mode=None):
    normalized = _normalize_mode(mode)
    return THEME_COLORS.get(normalized, THEME_COLORS["dark"]).copy()


def apply_default_theme(app):
    try:
        apply_appearance_mode("dark", app)
        ctk.set_default_color_theme("blue")
    except Exception:
        pass


def apply_light_theme(app):
    try:
        apply_appearance_mode("light", app)
    except Exception:
        pass


def toggle_theme(app):
    try:
        current = ctk.get_appearance_mode()
        target = "light" if str(current).lower() == "dark" else "dark"
        apply_appearance_mode(target, app)
    except Exception:
        pass
