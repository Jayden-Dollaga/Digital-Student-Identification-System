"""Launcher for the PySide6-based Qt interface.

This module is the entry point for the modern desktop UI. It loads the
stylesheet, creates the main window, and starts the Qt application loop.
It is intentionally separate from the legacy CustomTkinter interface so the
new UI can be tested and iterated without replacing the older workflow.
"""

import atexit
import sys
import threading
import traceback
from pathlib import Path
from typing import Any
from PySide6.QtWidgets import QApplication

from core.logger import log
from gui_qt.main_window import MainWindow
from settings_store import load_settings


def _handle_uncaught_exception(exc_type: type[BaseException], exc_value: BaseException, exc_traceback: Any) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    log.exception(
        "Uncaught exception in main thread",
        error=str(exc_value),
        traceback="".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
    )


def _handle_thread_exception(args: threading.ExceptHookArgs) -> None:
    thread = getattr(args, "thread", None)
    if thread is None:
        log.exception(
            "Uncaught exception in thread",
            error=str(args.exc_value),
            traceback="".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)),
        )
        return

    log.exception(
        "Uncaught exception in thread",
        thread_name=getattr(thread, "name", "unknown"),
        thread_id=getattr(thread, "ident", None),
        error=str(args.exc_value),
        traceback="".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)),
    )


def _on_app_about_to_quit() -> None:
    log.info("QApplication aboutToQuit", thread_id=threading.get_ident(), thread_name=threading.current_thread().name)


def _on_process_exit() -> None:
    log.info("Process exit via atexit", thread_id=threading.get_ident(), thread_name=threading.current_thread().name)


def load_stylesheet(app: QApplication, theme: str = "dark"):
    theme_file = "theme_light.qss" if theme.lower() == "light" else "theme.qss"
    qss_path = Path(__file__).parent / theme_file
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8", errors="replace"))
    elif theme.lower() == "light":
        app.setStyleSheet("")


def main():
    sys.excepthook = _handle_uncaught_exception
    threading.excepthook = _handle_thread_exception
    atexit.register(_on_process_exit)

    log.info("main() entered", thread_id=threading.get_ident(), thread_name=threading.current_thread().name)

    try:
        app = QApplication(sys.argv)
        log.info("QApplication created", thread_id=threading.get_ident(), thread_name=threading.current_thread().name)
        app.aboutToQuit.connect(_on_app_about_to_quit)

        settings = load_settings()
        load_stylesheet(app, settings.get("theme", "dark"))

        window = MainWindow()
        log.info("MainWindow created", thread_id=threading.get_ident(), thread_name=threading.current_thread().name)
        window.show()
        log.info("MainWindow shown", thread_id=threading.get_ident(), thread_name=threading.current_thread().name)

        result = app.exec()
        log.info("QApplication.exec() returned", result=result)
        log.info("main() returning", thread_id=threading.get_ident(), thread_name=threading.current_thread().name)
        sys.exit(result)
    except SystemExit:
        raise
    except Exception as exc:
        # Previously, any exception raised before app.exec() started (a bad
        # setting, a locked file, a widget failing to construct, etc.) just
        # crashed the process with nothing but a console traceback - which
        # looks exactly like "the app closes immediately" if there's no
        # console window attached (e.g. launched by double-click). Now it's
        # logged AND shown to the user instead of vanishing silently.
        log.exception("Fatal error during startup", error=str(exc))
        try:
            from PySide6.QtWidgets import QMessageBox
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Startup Error",
                "The application failed to start:\n\n"
                f"{exc}\n\n"
                "Details were written to data/logs/ - check the latest log file.",
            )
        except Exception:
            print(f"[FATAL] Application failed to start: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()