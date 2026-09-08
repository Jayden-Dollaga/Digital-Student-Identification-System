"""Compatibility entry point for the maintained V3 application."""


def main() -> None:
    """Launch the HTML/pywebview interface."""
    from gui_web.main_web import main as launch_web_gui

    launch_web_gui()


if __name__ == "__main__":
    main()
