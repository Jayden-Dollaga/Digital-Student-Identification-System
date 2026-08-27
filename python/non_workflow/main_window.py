"""Historical non-workflow window retained outside the active Qt path."""

"""Compatibility wrapper exposing the current GUI application."""

from gui.app import FingerprintApp, main


def run_gui():
    app = FingerprintApp()
    app.mainloop()


__all__ = ["FingerprintApp", "main", "run_gui"]
