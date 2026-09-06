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
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory

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


def apply_base_style(app: QApplication) -> None:
    """Force the "Fusion" widget style before any stylesheet is applied.

    Without this, Qt defaults to the native platform style (e.g. "windowsvista"
    on Windows), which paints certain widgets - QDialog and QMessageBox chief
    among them - using the *current user's OS theme* instead of our QSS. That
    is why dialogs like "Confirm Wipe" or "No selection" showed up as plain
    white/native boxes with washed-out text: the native style ignored our
    dark background rules and only the universal text-color rule got through.

    Fusion is a style Qt renders entirely itself, so it honors our stylesheet
    fully and identically regardless of the host machine's OS theme, Windows
    build, or dark/light system setting - which is what makes the UI look the
    same on every PC instead of depending on that PC's own theme.
    """
    if "Fusion" in QStyleFactory.keys():
        app.setStyle(QStyleFactory.create("Fusion"))


def _build_palette(theme: str) -> QPalette:
    """Build a QPalette that matches our QSS colors exactly.

    Fusion draws its *own* colors, but it still starts from
    ``QApplication.palette()`` for anything our stylesheet doesn't touch -
    a plain QWidget container, a QScrollArea viewport, a QTableView's
    blank area past the last row, etc. On Qt6 that default palette is
    seeded from the *host OS's* current light/dark setting. That's exactly
    why the Students/Settings pages showed up light on the test PC
    (its Windows theme is Light) while other pages that happen to be fully
    covered by named QSS rules looked fine: the gap was in colors, not in
    the style engine.

    Setting an explicit palette here removes that gap entirely - every
    color Qt could possibly fall back to is pinned to our own theme, so
    the app looks identical no matter what theme the PC it runs on is
    set to.
    """
    palette = QPalette()

    if theme.lower() == "light":
        window = QColor("#F3F4F6")
        base = QColor("#FFFFFF")
        alt_base = QColor("#F3F4F6")
        text = QColor("#111827")
        disabled_text = QColor("#9CA3AF")
        button = QColor("#E5E7EB")
        highlight = QColor("#2563EB")
        highlighted_text = QColor("#FFFFFF")
        tooltip_base = QColor("#FFFFFF")
    else:
        window = QColor("#14161A")
        base = QColor("#1B1E24")
        alt_base = QColor("#20242B")
        text = QColor("#E6E8EB")
        disabled_text = QColor("#5B6169")
        button = QColor("#2A3038")
        highlight = QColor("#4C8DFF")
        highlighted_text = QColor("#0B1220")
        tooltip_base = QColor("#1B1E24")

    palette.setColor(QPalette.ColorRole.Window, window)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, base)
    palette.setColor(QPalette.ColorRole.AlternateBase, alt_base)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, button)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, text)
    palette.setColor(QPalette.ColorRole.ToolTipBase, tooltip_base)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.PlaceholderText, disabled_text)
    palette.setColor(QPalette.ColorRole.Highlight, highlight)
    palette.setColor(QPalette.ColorRole.HighlightedText, highlighted_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_text)

    return palette


def apply_theme(app: QApplication, theme: str = "dark") -> None:
    """Apply both the QPalette and the QSS for the given theme together.

    These two must always be set as a pair - the palette is the fallback
    for anything the stylesheet doesn't explicitly color, so an app-wide
    theme switch (or a fresh install on a new PC) can never end up with
    one page pinned to our colors and another leaking the OS's.
    """
    app.setPalette(_build_palette(theme))
    load_stylesheet(app, theme)


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
        apply_base_style(app)

        settings = load_settings()
        apply_theme(app, settings.get("theme", "dark"))

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
            apply_base_style(app)
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