"""Launcher for the HTML/pywebview-based v3 interface.

This is the v3 counterpart to python/gui_qt/main_qt.py (v2, now archived
under archive/legacy-ui/v2) and the old python/main.py (v1, archived under
archive/legacy-ui/v1). It opens a native window (via pywebview) that loads
web/index.html, and exposes the Api class from api.py as
``window.pywebview.api`` so the page's JavaScript can call straight into
the existing backend (core.database, core.serial_handler, etc.).

Run with:  python run_web_gui.py   (from the project root)
       or: python python/gui_web/main_web.py
"""

import sys
import threading
import traceback
from pathlib import Path

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from run_web_gui import main as launch_with_preflight

    launch_with_preflight()
    raise SystemExit(0)

import webview

try:
    from .api import Api
    from ..core.logger import log
except ImportError:  # pragma: no cover - direct script execution fallback
    from api import Api
    from core.logger import log


def resolve_window_size(screen_width: int | None = None, screen_height: int | None = None) -> tuple[int, int]:
    """Return a window size that fits the current display without clipping controls."""
    if screen_width is None or screen_height is None:
        screen_width = 1280
        screen_height = 800
        try:
            screens = getattr(webview, "screens", None) or []
            if screens:
                primary = screens[0]
                screen_width = int(getattr(primary, "width", screen_width) or screen_width)
                screen_height = int(getattr(primary, "height", screen_height) or screen_height)
        except Exception:
            pass

    screen_width = max(760, int(screen_width))
    screen_height = max(540, int(screen_height))

    width = min(screen_width - 40, 1180)
    height = min(screen_height - 40, 740)

    width = max(760, width)
    height = max(540, height)
    return width, height


def _logo_path() -> Path:
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return bundle_root / "assets" / "icon" / "DSIS_LOGO.ico"


def _handle_uncaught_exception(exc_type, exc_value, exc_traceback) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    log.exception(
        "Uncaught exception in main thread",
        error=str(exc_value),
        traceback="".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
    )


def _handle_thread_exception(args: threading.ExceptHookArgs) -> None:
    log.exception(
        "Uncaught exception in thread",
        thread_name=getattr(args.thread, "name", "unknown"),
        error=str(args.exc_value),
        traceback="".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)),
    )


def main() -> None:
    sys.excepthook = _handle_uncaught_exception
    threading.excepthook = _handle_thread_exception

    log.info("DSIS v3 (web) starting")

    api = Api()
    web_dir = Path(__file__).parent / "web"
    index_path = web_dir / "index.html"
    width, height = resolve_window_size()

    window = webview.create_window(
        title="DSIS \u2014 Digital Student Identification System",
        url=str(index_path),
        js_api=api,
        width=width,
        height=height,
        min_size=(760, 540),
    )
    api.set_window(window)

    def _on_closed() -> None:
        try:
            api._disconnect_impl()
        except Exception:
            pass
        log.info("DSIS v3 (web) window closed")

    window.events.closed += _on_closed

    webview.start(debug=False, icon=str(_logo_path()))


if __name__ == "__main__":
    main()
