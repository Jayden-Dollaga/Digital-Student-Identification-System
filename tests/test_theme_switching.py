import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from gui import theme as theme_module


class DummyApp:
    def __init__(self):
        self.scheduled = []

    def after(self, ms, callback, *args):
        self.scheduled.append((ms, callback, args))

    def winfo_exists(self):
        return True

    def update_idletasks(self):
        return None


def test_apply_appearance_mode_schedules_safe_theme_change(monkeypatch):
    calls = []

    def fake_set_appearance_mode(mode):
        calls.append(mode)

    monkeypatch.setattr(theme_module.ctk, "set_appearance_mode", fake_set_appearance_mode)

    app = DummyApp()
    theme_module.apply_appearance_mode("Light", app)

    assert len(app.scheduled) == 1

    app.scheduled[0][1]()
    assert calls == ["light"]


def test_get_theme_colors_returns_mode_specific_values():
    dark_colors = theme_module.get_theme_colors("dark")
    light_colors = theme_module.get_theme_colors("light")

    assert dark_colors["muted_text"] == "#8b8c8d"
    assert light_colors["muted_text"] == "#64748b"
    assert dark_colors["card_background"] == "#2a2a2a"
    assert light_colors["card_background"] == "#f8fafc"
