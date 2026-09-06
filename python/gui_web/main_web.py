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

import webview

from api import Api
from core.logger import log


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

    window = webview.create_window(
        title="DSIS \u2014 Digital Student Identification System",
        url=str(index_path),
        js_api=api,
        width=1180,
        height=740,
        min_size=(900, 600),
    )
    api.set_window(window)

    def _on_closed() -> None:
        try:
            api.disconnect()
        except Exception:
            pass
        log.info("DSIS v3 (web) window closed")

    window.events.closed += _on_closed

    webview.start(debug=False)


if __name__ == "__main__":
    main()
