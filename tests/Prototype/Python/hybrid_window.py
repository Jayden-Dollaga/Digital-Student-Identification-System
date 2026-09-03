"""Second UI concept: the prototype identification flow combined with the app shell."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QListWidget,
    QMainWindow, QPushButton, QStackedWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from prototype_window import MOCK_RESULTS, PrototypeWindow


class HybridWindow(PrototypeWindow):
    """Standalone comparison concept; it does not start serial or database services."""

    NAVIGATION = ("Dashboard", "Identify", "Attendance", "Students", "Reports", "Logs", "Settings")

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DSIS Hybrid Prototype - Digital Student Identification System")
        self.resize(1240, 780)

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("prototypeSidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 18, 12, 14)
        layout.setSpacing(4)

        brand = QHBoxLayout()
        brand.setSpacing(10)
        from prototype_window import LogoMark
        brand.addWidget(LogoMark())
        brand_text = QVBoxLayout()
        self.brand_title = QLabel("DSIS")
        self.brand_title.setObjectName("brandTitle")
        brand_text.addWidget(self.brand_title)
        self.brand_caption = QLabel("Digital student identification")
        self.brand_caption.setObjectName("mutedText")
        brand_text.addWidget(self.brand_caption)
        brand.addLayout(brand_text)
        layout.addLayout(brand)

        section = QLabel("SYSTEM")
        section.setObjectName("sectionLabel")
        layout.addWidget(section)
        self._nav_buttons = []
        for index, name in enumerate(self.NAVIGATION, 1):
            button = QPushButton(name)
            button.setObjectName("navButton")
            button.setProperty("navCode", f"{index:02d}")
            button.setProperty("navName", name)
            button.setCheckable(True)
            button.setChecked(name == "Dashboard")
            button.clicked.connect(lambda _checked, page=name: self._select_page(page))
            self._nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch()
        self.density_button = QPushButton("Use compact density")
        self.density_button.setObjectName("densityButton")
        self.density_button.setCheckable(True)
        self.density_button.toggled.connect(self._set_compact)
        layout.addWidget(self.density_button)
        return sidebar

    def _build_header(self):
        header = QWidget()
        header.setObjectName("prototypeHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(26, 14, 26, 14)
        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("pageTitle")
        layout.addWidget(self.page_title)
        layout.addStretch()
        self.connection_label = QLabel("●  Device connected")
        self.connection_label.setObjectName("onlineState")
        layout.addWidget(self.connection_label)
        device = QLabel("ESP32-FP-01  |  COM7  |  115200 baud")
        device.setObjectName("mutedText")
        layout.addWidget(device)
        self.connect_button = QPushButton("Disconnect")
        self.connect_button.setObjectName("secondaryButton")
        self.connect_button.clicked.connect(self._toggle_connection)
        layout.addWidget(self.connect_button)
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
        self.identification_page = self._build_identification_page()
        self.attendance_page = self._build_attendance_page()
        self.students_page = self._build_students_page()
        self.reports_page = self._build_reports_page()
        self.logs_page = self._build_logs_page()
        self.settings_page = self._build_settings_page()
        for page in (self.dashboard_page, self.identification_page, self.attendance_page,
                     self.students_page, self.reports_page, self.logs_page, self.settings_page):
            self.stack.addWidget(page)

    def _build_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(16)
        layout.addWidget(QLabel("Overview", objectName="contentTitle"))
        layout.addWidget(QLabel("A quick view of today’s identification activity and device health.", objectName="mutedText"))
        cards = QHBoxLayout()
        for title, value, note in (("Identifications today", "184", "+12% from yesterday"), ("Registered students", "642", "638 templates active"), ("Device status", "Online", "Last response 08:42:16")):
            panel, panel_layout = self._panel(title)
            panel_layout.addWidget(QLabel(value, objectName="metricValue"))
            panel_layout.addWidget(QLabel(note, objectName="mutedText"))
            cards.addWidget(panel)
        layout.addLayout(cards)
        panel, panel_layout = self._panel("Latest activity")
        activity = QListWidget()
        for row in MOCK_RESULTS:
            activity.addItem(f"{row[3]}   {row[0]}   |   {row[5]}   |   {row[4]}")
        panel_layout.addWidget(activity)
        layout.addWidget(panel, 1)
        return page

    def _build_attendance_page(self):
        return self._build_table_page("Attendance", ("Time", "Student", "ID", "Confidence", "Status"), MOCK_RESULTS)

    def _build_students_page(self):
        return self._build_table_page("Students", ("Student", "Student ID", "Program", "Fingerprint"), (("Amina Reyes", "STU-2024-0187", "BS IT", "Active"), ("Noah Santos", "STU-2024-0142", "BS CS", "Active"), ("Mikaela Cruz", "STU-2023-0098", "BS IT", "Active"), ("Liam Flores", "STU-2024-0219", "BS IT", "Needs enrollment")))

    def _build_table_page(self, title, headers, rows):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(26, 22, 26, 22)
        heading = QHBoxLayout()
        heading.addWidget(QLabel(title, objectName="contentTitle"))
        heading.addStretch()
        heading.addWidget(QPushButton("Export CSV", objectName="secondaryButton"))
        layout.addLayout(heading)
        table = QTableWidget(len(rows), len(headers))
        table.setObjectName("studentTable")
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        for row_index, row in enumerate(rows):
            values = row if title == "Students" else (row[3], row[0], row[1], row[4], row[5])
            for column_index, value in enumerate(values):
                table.setItem(row_index, column_index, QTableWidgetItem(value))
        layout.addWidget(table)
        return page

    def _build_reports_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.addWidget(QLabel("Reports", objectName="contentTitle"))
        layout.addWidget(QLabel("Prepare attendance summaries for review or export.", objectName="mutedText"))
        panel, panel_layout = self._panel("Report builder")
        for label in ("Date range: Today", "Format: CSV", "Records available: 184"):
            panel_layout.addWidget(QLabel(label, objectName="detailValue"))
        panel_layout.addWidget(QPushButton("Generate report", objectName="primaryButton"))
        layout.addWidget(panel)
        layout.addStretch()
        return page

    def _build_logs_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.addWidget(QLabel("Logs", objectName="contentTitle"))
        log = QListWidget()
        for line in ("08:42:16  INFO  Identification matched Amina Reyes", "08:41:58  INFO  Sensor heartbeat received", "08:40:02  INFO  Database sync completed"):
            log.addItem(line)
        layout.addWidget(log)
        return page

    def _build_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.addWidget(QLabel("Settings", objectName="contentTitle"))
        panel, panel_layout = self._panel("Application settings")
        for text, checked in (("Auto-detect ESP32 on connect", True), ("Start in identification mode", True), ("Create automatic backups", True)):
            option = QCheckBox(text)
            option.setChecked(checked)
            panel_layout.addWidget(option)
        row = QHBoxLayout()
        row.addWidget(QLabel("Theme", objectName="mutedText"))
        row.addStretch()
        theme = QComboBox()
        theme.addItems(("Dark", "Light"))
        row.addWidget(theme)
        panel_layout.addLayout(row)
        layout.addWidget(panel)
        layout.addStretch()
        return page

    def _select_page(self, name):
        index = {page: index for index, page in enumerate(self.NAVIGATION)}[name]
        self.stack.setCurrentIndex(index)
        self.page_title.setText(name)
        for button in self._nav_buttons:
            button.setChecked(button.property("navName") == name)

    def _apply_density(self):
        self.sidebar.setFixedWidth(188 if not self._compact else 136)
        self.density_button.setText("Use comfortable density" if self._compact else "Use compact density")
        for button in self._nav_buttons:
            button.setText(button.property("navCode") if self._compact else button.property("navName"))
            button.setToolTip(button.property("navName"))
        if hasattr(self, "results"):
            self.results.setSpacing(0 if self._compact else 2)
            self.results.setUniformItemSizes(self._compact)

    def _toggle_connection(self):
        connected = self.connect_button.text() == "Disconnect"
        self.connect_button.setText("Connect" if connected else "Disconnect")
        self.connection_label.setText("●  Device disconnected" if connected else "●  Device connected")
        self.connection_label.setProperty("offline", connected)
        self.connection_label.style().unpolish(self.connection_label)
        self.connection_label.style().polish(self.connection_label)

    def _finish_scan(self):
        super()._finish_scan()
        self._select_page("Identify")


def apply_hybrid_style(app):
    app.setStyleSheet(
        """* { font-family: 'Segoe UI'; color: #D9E1EA; font-size: 13px; }
        QMainWindow, QWidget#prototypeRoot { background: #11161C; }
        QWidget#prototypeSidebar { background: #18212A; border-right: 1px solid #2B3843; }
        QLabel#brandTitle { color: #F4F7FA; font-size: 18px; font-weight: 700; }
        QLabel#mutedText { color: #8493A1; }
        QLabel#sectionLabel { color: #637381; font-size: 10px; font-weight: 700; margin: 18px 4px 5px; }
        QPushButton#navButton { background: transparent; border: 0; border-radius: 5px; text-align: left; padding: 9px 12px; color: #A9B7C4; }
        QPushButton#navButton:hover { background: #22303B; color: #F4F7FA; }
        QPushButton#navButton:checked { background: #244A70; color: #FFFFFF; border-left: 3px solid #59A5F5; }
        QPushButton#densityButton, QPushButton#secondaryButton { background: #263541; border: 1px solid #3A4D5B; border-radius: 4px; padding: 8px 12px; color: #D9E1EA; }
        QWidget#prototypeHeader { background: #11161C; border-bottom: 1px solid #2B3843; }
        QLabel#pageTitle { color: #F4F7FA; font-size: 20px; font-weight: 600; }
        QLabel#onlineState { color: #5BD18A; background: #173D2B; padding: 5px 8px; border-radius: 3px; font-size: 10px; font-weight: 700; }
        QLabel#onlineState[offline="true"] { color: #F17C7C; background: #4A2226; }
        QLabel#contentTitle { color: #F4F7FA; font-size: 17px; font-weight: 600; }
        QFrame#panel, QFrame#metric { background: #18212A; border: 1px solid #2B3843; border-radius: 5px; }
        QLabel#panelTitle { color: #A9B7C4; font-size: 12px; font-weight: 700; }
        QLabel#metricValue { color: #F4F7FA; font-size: 23px; font-weight: 600; }
        QLabel#sensorReady { color: #5BD18A; background: #173D2B; border: 1px solid #286443; border-radius: 5px; font-size: 22px; font-weight: 700; }
        QLabel#matchState { color: #5BD18A; background: #173D2B; padding: 5px 8px; border-radius: 3px; font-size: 10px; font-weight: 700; }
        QLabel#matchName { color: #F4F7FA; font-size: 24px; font-weight: 600; }
        QLabel#detailValue { color: #E8EDF2; font-weight: 600; }
        QPushButton#primaryButton { background: #2F80ED; color: #FFFFFF; border: 0; border-radius: 4px; padding: 9px 16px; font-weight: 600; }
        QListWidget, QTableWidget#studentTable { background: #141C23; border: 1px solid #2B3843; border-radius: 4px; }
        QListWidget::item { padding: 8px; border-bottom: 1px solid #26343F; }
        QListWidget::item:selected { background: #244A70; }
        QTableWidget#studentTable QHeaderView::section { background: #202D38; color: #A9B7C4; padding: 8px; border: 0; }
        QProgressBar { background: #24313B; border: 0; border-radius: 3px; height: 6px; }
        QProgressBar::chunk { background: #5BD18A; border-radius: 3px; }
        QWidget#statusBar { background: #18212A; border-top: 1px solid #2B3843; }
        """
    )


def main():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    apply_hybrid_style(app)
    window = HybridWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    main()
