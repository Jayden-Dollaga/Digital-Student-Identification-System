"""
Lightweight shim for `customtkinter` used during tests.

This shim implements a minimal subset of the CustomTkinter API by delegating
to the standard library's `tkinter`. It allows unit tests to import and
instantiate the legacy GUI without requiring the external `customtkinter`
package or native wheels.
"""
import tkinter as tk

_appearance_mode = "Light"


class CTk(tk.Tk):
    pass


class CTkFrame(tk.Frame):
    pass


class CTkLabel(tk.Label):
    pass


class CTkButton(tk.Button):
    pass


def set_default_color_theme(theme_name: str) -> None:
    # No-op for tests
    return None


def set_appearance_mode(mode: str) -> None:
    global _appearance_mode
    _appearance_mode = mode


def get_appearance_mode() -> str:
    return _appearance_mode

