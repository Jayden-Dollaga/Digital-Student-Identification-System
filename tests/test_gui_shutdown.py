import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

try:
    import tkinter as tk
except Exception:
    tk = None


def create_app_or_skip(testcase):
    tcl_root = Path(sys.executable).resolve().parent / "tcl" / "tcl8.6"
    if not (tcl_root / "init.tcl").is_file():
        testcase.skipTest(f"Archived GUI requires a readable Tcl runtime at {tcl_root}")
    if tk is not None:
        try:
            tk.Tcl().eval("info patchlevel")
            probe = tk.Tk()
            probe.withdraw()
            probe.destroy()
        except Exception as exc:
            testcase.skipTest(f"Archived GUI requires an initializable Tcl runtime: {exc}")
    try:
        from gui.app import FingerprintApp
    except Exception as exc:
        testcase.skipTest(f"Tkinter/customtkinter unavailable: {exc}")

    try:
        return FingerprintApp()
    except Exception as exc:
        testcase.skipTest(f"Unable to create GUI window: {exc}")


class GuiShutdownTest(unittest.TestCase):
    def test_quit_app_marks_shutdown_and_closes_window(self):
        app = create_app_or_skip(self)
        try:
            app.quit_app()
            self.assertTrue(app._closing)
            if tk is not None:
                with self.assertRaises(tk.TclError):
                    app.winfo_exists()
        finally:
            try:
                if app.winfo_exists():
                    app.destroy()
            except Exception:
                pass

    def test_append_log_message_after_destroy_is_safe(self):
        app = create_app_or_skip(self)
        try:
            app.quit_app()
            app._append_log_message("late log update")
        finally:
            try:
                if app.winfo_exists():
                    app.destroy()
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
