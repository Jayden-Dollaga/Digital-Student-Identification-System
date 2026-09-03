"""Standalone reconstruction of the original DSIS desktop UI."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QStyle, QVBoxLayout, QWidget

from hybrid_window import HybridWindow
from prototype_window import LogoMark


class OriginalUIWindow(HybridWindow):
    """The original six-page DSIS shell, kept separate for visual comparison."""

    NAVIGATION = ("Dashboard", "Attendance", "Students", "Reports", "Logs", "Settings")
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
        self.setWindowTitle("Digital Student Identification System")
        self.resize(1180, 720)

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("prototypeSidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(5)

        brand = QVBoxLayout()
        brand.setSpacing(8)
        brand.addWidget(LogoMark(), alignment=Qt.AlignmentFlag.AlignHCenter)
        self.brand_title = QLabel("DSIS")
        self.brand_title.setObjectName("brandTitle")
        self.brand_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        brand.addWidget(self.brand_title)
        self.brand_caption = QLabel("Digital Student Identification System")
        self.brand_caption.setObjectName("mutedText")
        self.brand_caption.setWordWrap(True)
        self.brand_caption.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        brand.addWidget(self.brand_caption)
        layout.addLayout(brand)

        section = QLabel("MAIN MENU")
        section.setObjectName("sectionLabel")
        layout.addWidget(section)
        self._nav_buttons = []
        for index, name in enumerate(self.NAVIGATION, 1):
            button = QPushButton(name)
            button.setObjectName("navButton")
            button.setProperty("navCode", f"{index:02d}")
            button.setProperty("navName", name)
            button.setIcon(QApplication.style().standardIcon(self.NAV_ICONS[index - 1]))
            button.setCheckable(True)
            button.setChecked(name == "Dashboard")
            button.setToolTip(name)
            button.clicked.connect(lambda _checked, page=name: self._select_page(page))
            self._nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch()
        self.density_button = QPushButton("Compact sidebar")
        self.density_button.setObjectName("densityButton")
        self.density_button.setCheckable(True)
        self.density_button.toggled.connect(self._set_compact)
        layout.addWidget(self.density_button)
        return sidebar

    def _build_header(self):
        header = QWidget()
        header.setObjectName("prototypeHeader")
        layout = QVBoxLayout(header)
        layout.setContentsMargins(24, 10, 24, 10)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("pageTitle")
        top_row.addWidget(self.page_title)
        top_row.addStretch()
        self.connection_label = QLabel("Disconnected")
        self.connection_label.setObjectName("offlineState")
        top_row.addWidget(self.connection_label)
        self.connect_button = QPushButton("Connect")
        self.connect_button.setObjectName("primaryButton")
        self.connect_button.clicked.connect(self._toggle_connection)
        top_row.addWidget(self.connect_button)
        layout.addLayout(top_row)

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(QLabel("Device: ESP32 Fingerprint Module", objectName="mutedText"))
        bottom_row.addStretch()
        bottom_row.addWidget(QLabel("Port: Auto-detect", objectName="mutedText"))
        self.scan_toggle_button = QPushButton("Start scan")
        self.scan_toggle_button.setObjectName("secondaryButton")
        self.scan_toggle_button.clicked.connect(self._select_page_identification)
        bottom_row.addWidget(self.scan_toggle_button)
        layout.addLayout(bottom_row)
        return header

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("prototypeRoot")
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.sidebar = self._build_sidebar()
        root_layout.addWidget(self.sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._build_header())
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        content_layout.addWidget(self._build_status_bar())
        root_layout.addWidget(content, 1)

        self.dashboard_page = self._build_dashboard_page()
        self.attendance_page = self._build_attendance_page()
        self.students_page = self._build_students_page()
        self.reports_page = self._build_reports_page()
        self.logs_page = self._build_logs_page()
        self.settings_page = self._build_settings_page()
        for page in (self.dashboard_page, self.attendance_page, self.students_page,
                     self.reports_page, self.logs_page, self.settings_page):
            self.stack.addWidget(page)

    def _select_page(self, name):
        index = {page: index for index, page in enumerate(self.NAVIGATION)}[name]
        self.stack.setCurrentIndex(index)
        self.page_title.setText(name)
        for button in self._nav_buttons:
            button.setChecked(button.property("navName") == name)

    def _select_page_identification(self):
        self._select_page("Attendance")

    def _toggle_connection(self):
        connected = self.connect_button.text() == "Disconnect"
        self.connect_button.setText("Connect" if connected else "Disconnect")
        self.connection_label.setText("Disconnected" if connected else "Connected")
        self.connection_label.setObjectName("offlineState" if connected else "onlineState")
        self.connection_label.style().unpolish(self.connection_label)
        self.connection_label.style().polish(self.connection_label)

    def _apply_density(self):
        self.sidebar.setFixedWidth(200 if not self._compact else 68)
        self.density_button.setText("Expand sidebar" if self._compact else "Compact sidebar")
        for button in self._nav_buttons:
            button.setText("" if self._compact else button.property("navName"))
            button.setIconSize(QSize(16, 16))
            button.setToolTip(button.property("navName"))
            button.setProperty("compact", self._compact)
            button.style().unpolish(button)
            button.style().polish(button)


def apply_original_style(app):
    app.setStyleSheet(
        """* { font-family: 'Segoe UI'; color: #E6E8EB; font-size: 13px; }
        QMainWindow, QWidget#prototypeRoot { background: #14161A; }
        QWidget#prototypeSidebar { background: #1B1E24; border-right: 1px solid #2B3038; }
        QLabel#brandTitle { color: #F2F3F5; font-size: 20px; font-weight: 700; }
        QLabel#mutedText { color: #8A909C; }
        QLabel#sectionLabel { color: #6F7784; font-size: 10px; font-weight: 700; margin: 18px 4px 6px; }
        QPushButton#navButton { background: transparent; border: 1px solid transparent; border-radius: 5px; text-align: left; padding: 10px 12px; color: #AEB4BD; }
        QPushButton#navButton:hover { background: #24282F; color: #F2F3F5; }
        QPushButton#navButton:checked { background: #243C60; color: #6BA1FF; border-left: 3px solid #4C8DFF; }
        QPushButton#navButton[compact="true"] { text-align: center; padding: 10px 0; }
        QPushButton#densityButton, QPushButton#secondaryButton { background: #2A3038; border: 1px solid #343C47; border-radius: 5px; padding: 8px 12px; color: #E6E8EB; }
        QWidget#prototypeHeader { background: #14161A; border-bottom: 1px solid #2B3038; }
        QLabel#pageTitle { color: #F2F3F5; font-size: 18px; font-weight: 600; }
        QLabel#offlineState, QLabel#onlineState { color: #F87171; background: #3D2024; padding: 5px 9px; border-radius: 4px; font-weight: 600; }
        QLabel#onlineState { color: #4ADE80; background: #173D2B; }
        QLabel#contentTitle { color: #F2F3F5; font-size: 17px; font-weight: 600; }
        QFrame#panel, QFrame#metric { background: #1B1E24; border: 1px solid #2B3038; border-radius: 6px; }
        QLabel#panelTitle { color: #AEB4BD; font-size: 12px; font-weight: 700; }
        QLabel#metricValue { color: #F2F3F5; font-size: 24px; font-weight: 700; }
        QLabel#sensorReady { color: #4ADE80; background: #173D2B; border: 1px solid #286443; border-radius: 5px; font-size: 22px; font-weight: 700; }
        QLabel#matchState { color: #4ADE80; background: #173D2B; padding: 5px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; }
        QLabel#matchName { color: #F2F3F5; font-size: 24px; font-weight: 600; }
        QLabel#detailValue { color: #E6E8EB; font-weight: 600; }
        QPushButton#primaryButton { background: #4C8DFF; color: #0B1220; border: 0; border-radius: 5px; padding: 9px 16px; font-weight: 600; }
        QListWidget, QTableWidget#studentTable { background: #171A20; border: 1px solid #2B3038; border-radius: 5px; }
        QListWidget::item { padding: 8px; border-bottom: 1px solid #262A31; }
        QListWidget::item:selected { background: #2D4B78; color: #F2F3F5; }
        QTableWidget#studentTable QHeaderView::section { background: #20242B; color: #AEB4BD; padding: 8px; border: 0; }
        QProgressBar { background: #20242B; border: 0; border-radius: 3px; height: 6px; }
        QProgressBar::chunk { background: #4C8DFF; border-radius: 3px; }
        QWidget#statusBar { background: #1B1E24; border-top: 1px solid #2B3038; }
        QLineEdit, QComboBox { background: #171A20; border: 1px solid #2A3038; border-radius: 5px; padding: 7px; color: #F2F3F5; }
        QCheckBox { color: #D8DEE9; padding: 5px 0; }
        """
    )


def main():
    app = QApplication.instance() or QApplication([])
    apply_original_style(app)
    window = OriginalUIWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    main()
