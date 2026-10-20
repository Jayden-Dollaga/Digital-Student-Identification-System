"""Launch the active HTML/pywebview DSIS interface (v3) from the repository root."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON_DIR = ROOT / "python"
GUI_WEB_DIR = PYTHON_DIR / "gui_web"

for path in (PYTHON_DIR, GUI_WEB_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from startup_preflight import format_preflight_report, run_environment_preflight


def _show_startup_error(message: str) -> None:
    """Keep packaged Windows users from losing startup errors with the console."""
    if not getattr(sys, "frozen", False) or not message:
        return
    try:
        # Use the native Windows dialog API instead of Tk so the active v3
        # runtime stays independent from the archived Tkinter interface.
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            None,
            str(message),
            "DSIS could not start",
            0x10,  # MB_ICONERROR
        )
    except Exception:
        # The console/log remains the fallback if the desktop session or
        # native dialog API is unavailable (for example, when running headless).
        pass


def main(preflight_runner=run_environment_preflight, app_launcher=None):
    try:
        report = preflight_runner()
        output = format_preflight_report(report)
        if output:
            print(output, file=sys.stderr)
        if not report.ok:
            _show_startup_error(output or "Startup checks failed. See the DSIS log for details.")
            raise SystemExit(1)

        if app_launcher is None:
            from gui_web.main_web import main as app_launcher

        app_launcher()
    except SystemExit:
        raise
    except Exception as exc:
        message = f"DSIS startup failed: {exc}\n\nSee the DSIS log for details."
        print(message, file=sys.stderr)
        _show_startup_error(message)
        raise


if __name__ == "__main__":
    main()
