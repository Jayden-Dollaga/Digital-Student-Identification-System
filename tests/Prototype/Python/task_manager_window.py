"""Windows 11 Task Manager-inspired DSIS comparison UI."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QStyle, QVBoxLayout, QWidget

from hybrid_window import HybridWindow
from prototype_window import LogoMark


class TaskManagerWindow(HybridWindow):
    """A separate shell variant with compact icon navigation and dense utility styling."""

    NAV_ICONS = {
        "Dashboard": QStyle.StandardPixmap.SP_ComputerIcon,
        "Identify": QStyle.StandardPixmap.SP_DialogApplyButton,
        "Attendance": QStyle.StandardPixmap.SP_FileDialogDetailedView,
        "Students": QStyle.StandardPixmap.SP_DirHomeIcon,
        "Reports": QStyle.StandardPixmap.SP_FileDialogListView,
        "Logs": QStyle.StandardPixmap.SP_FileDialogContentsView,
        "Settings": QStyle.StandardPixmap.SP_FileDialogInfoView,
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DSIS Task Manager UI - Digital Student Identification System")
        self.resize(1240, 780)

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("prototypeSidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 14, 10, 12)
        layout.setSpacing(3)

        brand = QVBoxLayout()
        brand.setSpacing(7)
        brand.addWidget(LogoMark(), alignment=Qt.AlignmentFlag.AlignHCenter)
        self.brand_title = QLabel("DSIS")
        self.brand_title.setObjectName("brandTitle")
        brand.addWidget(self.brand_title)
        self.brand_caption = QLabel("Student identification")
        self.brand_caption.setObjectName("mutedText")
        self.brand_caption.setWordWrap(True)
        brand.addWidget(self.brand_caption)
        layout.addLayout(brand)

        section = QLabel("APPROACHING TASKS")
        section.setObjectName("sectionLabel")
        layout.addWidget(section)

        self._nav_buttons = []
        app = QApplication.instance()
        for index, name in enumerate(self.NAVIGATION, 1):
            button = QPushButton(name)
            button.setObjectName("navButton")
            button.setProperty("navCode", f"{index:02d}")
            button.setProperty("navName", name)
            button.setIcon(app.style().standardIcon(self.NAV_ICONS[name]))
            button.setIconSize(QSize(18, 18))
            button.setCheckable(True)
            button.setChecked(name == "Dashboard")
            button.setToolTip(name)
            button.clicked.connect(lambda _checked, page=name: self._select_page(page))
            self._nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch()
        self.density_button = QPushButton("Compact mode")
        self.density_button.setObjectName("densityButton")
        self.density_button.setCheckable(True)
        self.density_button.toggled.connect(self._set_compact)
        layout.addWidget(self.density_button)
        return sidebar

    def _build_header(self):
        header = super()._build_header()
        self.connection_label.setText("Connected")
        return header

    def _apply_density(self):
        self.sidebar.setFixedWidth(208 if not self._compact else 64)
        self.density_button.setText("Comfortable mode" if self._compact else "Compact mode")
        for button in self._nav_buttons:
            button.setText("" if self._compact else button.property("navName"))
            button.setToolTip(button.property("navName"))
            button.setProperty("compact", self._compact)
            button.style().unpolish(button)
            button.style().polish(button)
        if hasattr(self, "results"):
            self.results.setSpacing(0 if self._compact else 2)
            self.results.setUniformItemSizes(self._compact)


def apply_task_manager_style(app):
    app.setStyleSheet(
        """* { font-family: 'Segoe UI'; color: #1F2933; font-size: 13px; }
        QMainWindow, QWidget#prototypeRoot { background: #F7F8FA; }
        QWidget#prototypeSidebar { background: #FFFFFF; border-right: 1px solid #D9DEE5; }
        QLabel#brandTitle { color: #1F2933; font-size: 18px; font-weight: 700; }
        QLabel#mutedText { color: #657383; }
        QLabel#sectionLabel { color: #788694; font-size: 10px; font-weight: 700; margin: 20px 5px 6px; }
        QPushButton#navButton { background: transparent; border: 0; border-radius: 4px; text-align: left; padding: 9px 10px; color: #4B5865; }
        QPushButton#navButton:hover { background: #F0F3F6; color: #1F2933; }
        QPushButton#navButton:checked { background: #E5F1FF; color: #0969DA; border-left: 3px solid #0969DA; }
        QPushButton#navButton[compact="true"] { text-align: center; padding: 10px 0; }
        QPushButton#densityButton, QPushButton#secondaryButton { background: #F1F3F5; border: 1px solid #D1D8E0; border-radius: 4px; padding: 8px 10px; color: #364250; }
        QWidget#prototypeHeader { background: #FFFFFF; border-bottom: 1px solid #D9DEE5; }
        QLabel#pageTitle { color: #1F2933; font-size: 20px; font-weight: 600; }
        QLabel#onlineState { color: #147A45; background: #E4F5EA; padding: 5px 8px; border-radius: 3px; font-size: 10px; font-weight: 700; }
        QLabel#contentTitle { color: #1F2933; font-size: 17px; font-weight: 600; }
        QFrame#panel, QFrame#metric { background: #FFFFFF; border: 1px solid #D9DEE5; border-radius: 4px; }
        QLabel#panelTitle { color: #536170; font-size: 12px; font-weight: 700; }
        QLabel#metricValue { color: #1F2933; font-size: 23px; font-weight: 600; }
        QLabel#sensorReady { color: #147A45; background: #E4F5EA; border: 1px solid #A9DDBD; border-radius: 4px; font-size: 22px; font-weight: 700; }
        QLabel#matchState { color: #147A45; background: #E4F5EA; padding: 5px 8px; border-radius: 3px; font-size: 10px; font-weight: 700; }
        QLabel#matchName { color: #1F2933; font-size: 24px; font-weight: 600; }
        QLabel#detailValue { color: #263442; font-weight: 600; }
        QPushButton#primaryButton { background: #0969DA; color: #FFFFFF; border: 0; border-radius: 4px; padding: 9px 16px; font-weight: 600; }
        QListWidget, QTableWidget#studentTable { background: #FFFFFF; border: 1px solid #D9DEE5; border-radius: 4px; }
        QListWidget::item { padding: 8px; border-bottom: 1px solid #E8EBEF; }
        QListWidget::item:selected { background: #E5F1FF; color: #1F2933; }
        QTableWidget#studentTable QHeaderView::section { background: #F1F3F5; color: #536170; padding: 8px; border: 0; }
        QProgressBar { background: #E5E9ED; border: 0; border-radius: 3px; height: 6px; }
        QProgressBar::chunk { background: #147A45; border-radius: 3px; }
        QWidget#statusBar { background: #FFFFFF; border-top: 1px solid #D9DEE5; }
        QLineEdit, QComboBox { background: #FFFFFF; border: 1px solid #C7CFD8; border-radius: 4px; padding: 7px; }
        QCheckBox { color: #364250; padding: 5px 0; }
        """
    )


def main():
    app = QApplication.instance() or QApplication([])
    apply_task_manager_style(app)
    window = TaskManagerWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    main()
