"""Display prototype combining the real DSIS pages with Task Manager styling."""

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QStyle

from actual_ui_prototype import ActualUIPrototypeWindow
from task_manager_window import apply_task_manager_style


class CombinedUIWindow(ActualUIPrototypeWindow):
    """Production page composition with a Windows 11 utility shell."""

    NAV_ICONS = (
        QStyle.StandardPixmap.SP_ComputerIcon,
        QStyle.StandardPixmap.SP_FileDialogDetailedView,
        QStyle.StandardPixmap.SP_DirHomeIcon,
        QStyle.StandardPixmap.SP_FileDialogListView,
        QStyle.StandardPixmap.SP_FileDialogContentsView,
        QStyle.StandardPixmap.SP_FileDialogInfoView,
    )

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DSIS Combined UI - Original Pages + Task Manager Shell")
        self.resize(1240, 760)
        self._add_navigation_icons()

    def _add_navigation_icons(self):
        buttons = self.sidebar._group.buttons()
        for button, icon in zip(buttons, self.NAV_ICONS):
            button.setIcon(QApplication.style().standardIcon(icon))
            button.setIconSize(QSize(18, 18))
            button.setToolTip(button.text())

    def _apply_compact_icon_state(self, compact):
        self.sidebar.set_compact(compact)
        for button in self.sidebar._group.buttons():
            button.setIconSize(QSize(18, 18))
            button.setToolTip(button.text())


def apply_combined_style(app):
    apply_task_manager_style(app)
    app.setStyleSheet(app.styleSheet() + """
        QWidget#centralWidget { background: #F7F8FA; }
        QWidget#sidebar { background: #FFFFFF; border-right: 1px solid #D9DEE5; }
        QLabel#sidebarTitle { color: #1F2933; font-size: 18px; font-weight: 700; }
        QLabel#brandMark { background: #0969DA; color: #FFFFFF; border-radius: 8px; }
        QLabel#sidebarSubtitle { color: #657383; }
        QFrame#sidebarDivider { background: #D9DEE5; }
        QPushButton#navButton { background: transparent; border: 0; border-radius: 4px; text-align: left; padding: 9px 10px; color: #4B5865; }
        QPushButton#navButton:hover { background: #F0F3F6; color: #1F2933; }
        QPushButton#navButton:checked { background: #E5F1FF; color: #0969DA; border-left: 3px solid #0969DA; }
        QWidget#headerBar { background: #FFFFFF; border-bottom: 1px solid #D9DEE5; }
        QLabel#deviceInfoLabel { color: #657383; }
        QLabel#pageTitle { color: #1F2933; font-size: 20px; font-weight: 600; }
        QFrame#card { background: #FFFFFF; border: 1px solid #D9DEE5; border-radius: 5px; }
        QTableWidget, QListWidget, QPlainTextEdit, QTextEdit { background: #FFFFFF; color: #1F2933; border: 1px solid #D9DEE5; }
        QWidget#statusBar { background: #FFFFFF; border-top: 1px solid #D9DEE5; }
    """)


def main():
    app = QApplication.instance() or QApplication([])
    apply_combined_style(app)
    window = CombinedUIWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    main()
