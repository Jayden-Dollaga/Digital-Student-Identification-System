import sys
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication, QLabel, QCheckBox, QTableWidget

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Python"))

from prototype_window import PrototypeWindow


class QtPrototypeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_prototype_contains_identification_surface_and_mock_results(self):
        window = PrototypeWindow()
        self.assertEqual(window.windowTitle().split(" - ")[0], "DSIS Prototype")
        self.assertEqual(window.stack.count(), 4)
        self.assertEqual(window.results.count(), 4)
        labels = [label.text() for label in window.findChildren(QLabel)]
        self.assertIn("Fingerprint identification", labels)
        self.assertIn("Amina Reyes", labels)
        window.close()

    def test_navigation_and_compact_density_are_interactive(self):
        window = PrototypeWindow()
        window._select_page("Settings")
        self.assertEqual(window.stack.currentIndex(), 3)
        original_width = window.sidebar.width()
        window.density_button.setChecked(True)
        self.assertTrue(window._compact)
        self.assertLess(window.sidebar.width(), original_width)
        self.assertEqual(window.density_button.text(), "Use comfortable density")
        window._select_page("Students")
        self.assertTrue(window._nav_buttons[2].isChecked())
        window.close()

    def test_selecting_result_updates_match_details(self):
        window = PrototypeWindow()
        window.results.setCurrentRow(3)
        self.assertEqual(window.match_name.text(), "Unregistered finger")
        self.assertEqual(window.match_state.text(), "REVIEW REQUIRED")
        self.assertEqual(window.match_id.text(), "No match")
        window.close()

    def test_secondary_pages_have_real_prototype_controls(self):
        window = PrototypeWindow()
        window._select_page("Students")
        self.assertEqual(len(window.findChildren(QTableWidget)), 1)
        window._select_page("Settings")
        self.assertEqual(len(window.findChildren(QCheckBox)), 3)
        window.close()

    def test_start_scan_enters_scanning_state(self):
        window = PrototypeWindow()
        window.scan_button.click()
        self.assertEqual(window.sensor_ready.text(), "SCANNING")
        self.assertEqual(window.scan_progress.value(), 35)
        window.close()


if __name__ == "__main__":
    unittest.main()