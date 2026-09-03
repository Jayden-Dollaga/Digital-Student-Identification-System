"""Standalone Task Manager-inspired identification UI prototype.

This module intentionally has no serial, database, or settings dependencies.
It is a visual and interaction test bed that can later be connected to the
existing application services once the structure is approved.
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QLineEdit, QMainWindow, QPushButton, QProgressBar,
    QSizePolicy, QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)


MOCK_RESULTS = [
    ("Amina Reyes", "STU-2024-0187", "BS Information Technology", "08:42:16", "98.7%", "Present"),
    ("Noah Santos", "STU-2024-0142", "BS Computer Science", "08:39:03", "96.4%", "Present"),
    ("Mikaela Cruz", "STU-2023-0098", "BS Information Technology", "08:31:44", "94.8%", "Present"),
    ("Unregistered finger", "No match", "Enrollment required", "08:27:12", "41.2%", "Review"),
]


class LogoMark(QWidget):
    """Asset-ready logo placeholder; replace its paint routine with a QPixmap later."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(38, 38)
        self.setObjectName("logoMark")

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#2F80ED"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(1, 1, 36, 36, 9, 9)
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.drawRoundedRect(10, 9, 18, 20, 5, 5)
        painter.drawLine(14, 33, 24, 33)


class PrototypeWindow(QMainWindow):
    density_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DSIS Prototype - Digital Student Identification System")
        self.resize(1180, 760)
        self.setMinimumSize(920, 600)
        self._compact = False
        self._nav_buttons = []
        self._build_ui()
        self._apply_density()

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

        self.identification_page = self._build_identification_page()
        self._add_placeholder_page("Activity", "Attendance events, device messages, and operator actions will appear here.")
        self._add_placeholder_page("Students", "Student records and enrollment management will appear here.")
        self._add_placeholder_page("Settings", "Connection, appearance, and backup preferences will appear here.")
        self.stack.insertWidget(0, self.identification_page)

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("prototypeSidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 18, 12, 14)
        layout.setSpacing(5)

        brand = QHBoxLayout()
        brand.setSpacing(10)
        brand.addWidget(LogoMark())
        brand_text = QVBoxLayout()
        self.brand_title = QLabel("DSIS")
        self.brand_title.setObjectName("brandTitle")
        brand_text.addWidget(self.brand_title)
        self.brand_caption = QLabel("Identification system")
        self.brand_caption.setObjectName("mutedText")
        brand_text.addWidget(self.brand_caption)
        brand.addLayout(brand_text)
        layout.addLayout(brand)

        section = QLabel("WORKSPACE")
        section.setObjectName("sectionLabel")
        layout.addWidget(section)
        for label in ("Identify", "Activity", "Students"):
            button = QPushButton(label)
            button.setProperty("navCode", {"Identify": "01", "Activity": "02", "Students": "03"}[label])
            button.setProperty("navName", label)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setChecked(label == "Identify")
            button.clicked.connect(lambda _checked, name=label: self._select_page(name))
            self._nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch()
        settings = QPushButton("Settings")
        settings.setProperty("navCode", "04")
        settings.setProperty("navName", "Settings")
        settings.setObjectName("navButton")
        settings.clicked.connect(lambda: self._select_page("Settings"))
        self._nav_buttons.append(settings)
        layout.addWidget(settings)

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
        layout.setContentsMargins(26, 18, 26, 16)
        self.page_title = QLabel("Identify")
        self.page_title.setObjectName("pageTitle")
        layout.addWidget(self.page_title)
        layout.addStretch()
        state = QLabel("  DEVICE ONLINE  ")
        state.setObjectName("onlineState")
        layout.addWidget(state)
        device = QLabel("ESP32-FP-01  |  USB Serial")
        device.setObjectName("mutedText")
        layout.addWidget(device)
        return header

    def _build_identification_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(26, 12, 26, 20)
        layout.setSpacing(16)

        intro = QHBoxLayout()
        intro_text = QVBoxLayout()
        title = QLabel("Fingerprint identification")
        title.setObjectName("contentTitle")
        intro_text.addWidget(title)
        subtitle = QLabel("Ready for the next scan. Place a registered finger on the sensor.")
        subtitle.setObjectName("mutedText")
        intro_text.addWidget(subtitle)
        intro.addLayout(intro_text)
        intro.addStretch()
        scan = QPushButton("Start scan")
        scan.setObjectName("primaryButton")
        scan.clicked.connect(self._simulate_scan)
        self.scan_button = scan
        intro.addWidget(scan)
        layout.addLayout(intro)

        metrics = QHBoxLayout()
        for label, value in (("TODAY", "184 scans"), ("MATCH RATE", "96.2%"), ("SENSOR", "AS608 / ready")):
            metric = QFrame()
            metric.setObjectName("metric")
            metric_layout = QVBoxLayout(metric)
            metric_layout.setContentsMargins(12, 8, 12, 8)
            metric_layout.setSpacing(2)
            metric_layout.addWidget(QLabel(label, objectName="metricLabel"))
            metric_layout.addWidget(QLabel(value, objectName="metricValue"))
            metrics.addWidget(metric)
        metrics.addStretch()
        layout.addLayout(metrics)

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._build_scan_panel(), 5)
        body.addWidget(self._build_details_panel(), 4)
        layout.addLayout(body, 1)

        recent = self._build_recent_panel()
        layout.addWidget(recent, 1)
        return page

    def _panel(self, title):
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        heading = QLabel(title)
        heading.setObjectName("panelTitle")
        layout.addWidget(heading)
        return panel, layout

    def _build_scan_panel(self):
        panel, layout = self._panel("Sensor status")
        layout.addStretch()
        visual = QLabel("READY")
        visual.setObjectName("sensorReady")
        visual.setAlignment(Qt.AlignmentFlag.AlignCenter)
        visual.setMinimumHeight(104)
        layout.addWidget(visual)
        hint = QLabel("Fingerprint sensor is connected and listening")
        hint.setObjectName("mutedText")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
        layout.addStretch()
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setTextVisible(False)
        progress.setObjectName("scanProgress")
        layout.addWidget(progress)
        self.scan_hint = QLabel("Last scan 08:42:16  |  98.7% confidence")
        self.scan_hint.setObjectName("mutedText")
        layout.addWidget(self.scan_hint)
        self.scan_progress = progress
        self.sensor_ready = visual
        self.sensor_hint = hint
        return panel

    def _build_details_panel(self):
        panel, layout = self._panel("Latest identification")
        self.match_state = QLabel("MATCH CONFIRMED")
        self.match_state.setObjectName("matchState")
        layout.addWidget(self.match_state)
        self.match_name = QLabel("Amina Reyes")
        self.match_name.setObjectName("matchName")
        layout.addWidget(self.match_name)
        self.match_id = QLabel("STU-2024-0187")
        self.match_id.setObjectName("mutedText")
        layout.addWidget(self.match_id)
        layout.addSpacing(8)
        for label, value in (("Program", "BS Information Technology"), ("Time", "08:42:16"), ("Confidence", "98.7%")):
            row = QHBoxLayout()
            key = QLabel(label)
            key.setObjectName("mutedText")
            val = QLabel(value)
            val.setObjectName("detailValue")
            row.addWidget(key)
            row.addStretch()
            row.addWidget(val)
            layout.addLayout(row)
        layout.addStretch()
        action = QPushButton("Open student record")
        action.setObjectName("secondaryButton")
        layout.addWidget(action)
        return panel

    def _build_recent_panel(self):
        panel, layout = self._panel("Recent identifications")
        self.results = QListWidget()
        self.results.setObjectName("resultsList")
        self.results.setSpacing(2)
        self.results.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        for name, student_id, program, time, confidence, status in MOCK_RESULTS:
            item = QListWidgetItem(f"{time}   {name}   |   {student_id}   |   {confidence}   {status}")
            item.setToolTip(f"{program} - {status}")
            self.results.addItem(item)
        self.results.currentRowChanged.connect(self._update_match)
        self.results.setCurrentRow(0)
        layout.addWidget(self.results)
        return panel

    def _build_status_bar(self):
        bar = QWidget()
        bar.setObjectName("statusBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(26, 8, 26, 8)
        layout.addWidget(QLabel("Today: 184 identifications"))
        layout.addStretch()
        layout.addWidget(QLabel("Database synced 2 min ago"))
        return bar

    def _add_placeholder_page(self, title, description):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 28, 30, 30)
        heading = QLabel(title)
        heading.setObjectName("contentTitle")
        layout.addWidget(heading)
        label = QLabel(description)
        label.setObjectName("mutedText")
        layout.addWidget(label)
        if title == "Activity":
            panel, panel_layout = self._panel("Identification events")
            activity = QListWidget()
            activity.setObjectName("resultsList")
            for row in MOCK_RESULTS:
                activity.addItem(f"{row[3]}   {row[0]}   |   {row[5]}   |   confidence {row[4]}")
            panel_layout.addWidget(activity)
        elif title == "Students":
            toolbar = QHBoxLayout()
            search = QLineEdit()
            search.setPlaceholderText("Search student name or ID")
            toolbar.addWidget(search, 1)
            enroll = QPushButton("New enrollment")
            enroll.setObjectName("primaryButton")
            toolbar.addWidget(enroll)
            layout.addLayout(toolbar)
            panel = QFrame()
            panel.setObjectName("panel")
            panel_layout = QVBoxLayout(panel)
            table = QTableWidget(4, 3)
            table.setHorizontalHeaderLabels(("Student", "ID", "Template"))
            table.setObjectName("studentTable")
            students = (("Amina Reyes", "STU-2024-0187", "Active"), ("Noah Santos", "STU-2024-0142", "Active"), ("Mikaela Cruz", "STU-2023-0098", "Active"), ("Liam Flores", "STU-2024-0219", "Needs enrollment"))
            for row_index, student in enumerate(students):
                for column_index, value in enumerate(student):
                    table.setItem(row_index, column_index, QTableWidgetItem(value))
            table.horizontalHeader().setStretchLastSection(True)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            panel_layout.addWidget(table)
        else:
            panel, panel_layout = self._panel("Prototype preferences")
            for text, checked in (("Start with device online", True), ("Play scan confirmation sound", False), ("Use automatic backups", True)):
                option = QCheckBox(text)
                option.setChecked(checked)
                panel_layout.addWidget(option)
            theme_row = QHBoxLayout()
            theme_row.addWidget(QLabel("Theme", objectName="mutedText"))
            theme_row.addStretch()
            theme_row.addWidget(QComboBox())
            theme_row.itemAt(2).widget().addItems(["Dark", "Light"])
            panel_layout.addLayout(theme_row)
        layout.addWidget(panel)
        layout.addStretch()
        self.stack.addWidget(page)

    def _select_page(self, name):
        index = {"Identify": 0, "Activity": 1, "Students": 2, "Settings": 3}[name]
        self.stack.setCurrentIndex(index)
        self.page_title.setText(name)
        for button in self._nav_buttons:
            button.setChecked(button.property("navName") == name)

    def _set_compact(self, compact):
        self._compact = compact
        self._apply_density()
        self.density_changed.emit(compact)

    def _apply_density(self):
        self.sidebar.setFixedWidth(188 if not self._compact else 136)
        self.density_button.setText("Use comfortable density" if self._compact else "Use compact density")
        for button in self._nav_buttons:
            button.setText(button.property("navCode") if self._compact else {
                "01": "Identify", "02": "Activity", "03": "Students", "04": "Settings"
            }.get(button.property("navCode"), button.text()))
            button.setToolTip({"01": "Identify", "02": "Activity", "03": "Students", "04": "Settings"}.get(button.property("navCode"), ""))
            button.setProperty("compact", self._compact)
            button.style().unpolish(button)
            button.style().polish(button)
        self.results.setSpacing(0 if self._compact else 2)
        self.results.setUniformItemSizes(self._compact)
        self.results.setStyleSheet("QListWidget::item { padding: 5px; }" if self._compact else "QListWidget::item { padding: 9px; }")

    def _update_match(self, row):
        if row < 0:
            return
        name, student_id, program, time, confidence, status = MOCK_RESULTS[row]
        is_match = status == "Present"
        self.match_state.setText("MATCH CONFIRMED" if is_match else "REVIEW REQUIRED")
        self.match_state.setProperty("review", not is_match)
        self.match_name.setText(name)
        self.match_id.setText(student_id)
        detail_values = self.findChildren(QLabel, "detailValue")
        if len(detail_values) >= 3:
            detail_values[0].setText(program)
            detail_values[1].setText(time)
            detail_values[2].setText(confidence)
        self.match_state.style().unpolish(self.match_state)
        self.match_state.style().polish(self.match_state)

    def _simulate_scan(self):
        self.scan_button.setEnabled(False)
        self.sensor_ready.setText("SCANNING")
        self.sensor_hint.setText("Keep your finger on the sensor")
        self.scan_progress.setValue(35)
        QTimer.singleShot(450, self._finish_scan)

    def _finish_scan(self):
        self.scan_progress.setValue(100)
        self.sensor_ready.setText("MATCH FOUND")
        self.sensor_hint.setText("Fingerprint captured and matched")
        self.scan_hint.setText("Scan complete 08:43:02  |  97.9% confidence")
        self.scan_button.setEnabled(True)


def main():
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(
        """* { font-family: 'Segoe UI'; color: #D9E1EA; font-size: 13px; }
        QMainWindow, QWidget#prototypeRoot { background: #11161C; }
        QWidget#prototypeSidebar { background: #18212A; border-right: 1px solid #2B3843; }
        QLabel#brandTitle { color: #F4F7FA; font-size: 18px; font-weight: 700; }
        QLabel#mutedText { color: #8493A1; }
        QLabel#sectionLabel { color: #637381; font-size: 10px; font-weight: 700; margin: 20px 4px 5px; }
        QPushButton#navButton { background: transparent; border: 0; border-radius: 5px; text-align: left; padding: 10px 12px; color: #A9B7C4; }
        QPushButton#navButton:hover { background: #22303B; color: #F4F7FA; }
        QPushButton#navButton:checked { background: #244A70; color: #FFFFFF; border-left: 3px solid #59A5F5; }
        QPushButton#densityButton { background: #202D38; border: 1px solid #334552; border-radius: 4px; padding: 7px; color: #A9B7C4; }
        QWidget#prototypeHeader { background: #11161C; border-bottom: 1px solid #2B3843; }
        QLabel#pageTitle { color: #F4F7FA; font-size: 20px; font-weight: 600; }
        QLabel#onlineState, QLabel#matchState { color: #5BD18A; background: #173D2B; padding: 5px 8px; border-radius: 3px; font-size: 10px; font-weight: 700; }
        QLabel#matchState[review="true"] { color: #F3C969; background: #4B3A17; }
        QLabel#contentTitle { color: #F4F7FA; font-size: 17px; font-weight: 600; }
        QFrame#metric { background: #18212A; border: 1px solid #2B3843; border-radius: 4px; min-width: 145px; }
        QLabel#metricLabel { color: #718291; font-size: 10px; font-weight: 700; }
        QLabel#metricValue { color: #E8EDF2; font-size: 14px; font-weight: 600; }
        QFrame#panel { background: #18212A; border: 1px solid #2B3843; border-radius: 5px; }
        QLabel#panelTitle { color: #A9B7C4; font-size: 12px; font-weight: 700; }
        QLabel#sensorReady { color: #5BD18A; background: #173D2B; border: 1px solid #286443; border-radius: 5px; font-size: 22px; font-weight: 700; }
        QLabel#matchName { color: #F4F7FA; font-size: 24px; font-weight: 600; }
        QLabel#detailValue { color: #E8EDF2; font-weight: 600; }
        QPushButton#primaryButton { background: #2F80ED; color: #FFFFFF; border: 0; border-radius: 4px; padding: 10px 18px; font-weight: 600; }
        QPushButton#secondaryButton { background: #263541; color: #D9E1EA; border: 1px solid #3A4D5B; border-radius: 4px; padding: 9px 12px; }
        QProgressBar#scanProgress { background: #24313B; border: 0; border-radius: 3px; height: 6px; }
        QProgressBar#scanProgress::chunk { background: #5BD18A; border-radius: 3px; }
        QListWidget#resultsList { background: #141C23; border: 1px solid #2B3843; border-radius: 4px; outline: 0; }
        QListWidget#resultsList::item { padding: 9px; border-bottom: 1px solid #26343F; }
        QListWidget#resultsList::item:selected { background: #244A70; }
        QTableWidget#studentTable { background: #141C23; border: 1px solid #2B3843; gridline-color: #26343F; }
        QTableWidget#studentTable QHeaderView::section { background: #202D38; color: #A9B7C4; padding: 8px; border: 0; }
        QWidget#statusBar { background: #18212A; border-top: 1px solid #2B3843; }
        """
    )
    window = PrototypeWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    main()