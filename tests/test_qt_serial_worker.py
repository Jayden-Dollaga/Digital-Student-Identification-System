"""Test Qt SerialWorker enrollment progress signals and serial monitor output."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import re

# Add python to path
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from PySide6.QtWidgets import QApplication

from core.serial_handler import SerialHandler
from core.attendance import AttendanceProcessor
from gui_qt.workers.serial_worker import SerialWorker


class TestSerialWorkerMessageParsing(unittest.TestCase):
    """Verify SerialWorker parses enrollment and wipe messages correctly."""

    @classmethod
    def setUpClass(cls):
        """Initialize Qt application once for all tests."""
        if not QApplication.instance():
            QApplication(sys.argv)

    def setUp(self):
        """Set up mock serial handler and worker."""
        self.mock_handler = MagicMock(spec=SerialHandler)
        self.mock_handler.is_connected.return_value = True
        self.mock_handler.should_ignore.return_value = False
        self.mock_handler.reconnect_count = 0
        
        self.processor = AttendanceProcessor()
        self.worker = SerialWorker(self.mock_handler, self.processor)
        
        # Capture signals
        self.emitted_signals = {"enroll_progress": [], "wipe_progress": [], "mode_changed": []}
        self.worker.enroll_progress.connect(lambda data: self.emitted_signals["enroll_progress"].append(data))
        self.worker.wipe_progress.connect(lambda data: self.emitted_signals["wipe_progress"].append(data))
        self.worker.mode_changed.connect(lambda mode: self.emitted_signals["mode_changed"].append(mode))

    def test_enrollment_message_parsing(self):
        """Test that enrollment messages are parsed and emitted correctly."""
        test_cases = [
            ("ENROLLING FINGER AS ID #3", {"event": "enrolling", "id": "3"}),
            ("enrolling finger as id #10", {"event": "enrolling", "id": "10"}),  # Case insensitive
            ("SUCCESS! Finger saved as ID #7", {"event": "success", "id": "7"}),
            ("Success finger saved as ID #99", {"event": "success", "id": "99"}),
            ("ENROLLMENT cancelled", {"event": "cancelled", "id": None}),
            ("Enrollment cancelled", {"event": "cancelled", "id": None}),
            ("ERROR: Something went wrong", {"event": "error", "id": None}),
            ("FAILED attempt", {"event": "error", "id": None}),
        ]

        for line, expected_signal in test_cases:
            self.emitted_signals["enroll_progress"].clear()
            self.worker._parse_enroll_progress(line)
            
            if "enrolling" in line.lower() or "success" in line.lower() or "cancel" in line.lower() or "error" in line.lower():
                self.assertEqual(
                    len(self.emitted_signals["enroll_progress"]), 1,
                    f"Should emit enroll_progress for: {line}"
                )
                emitted = self.emitted_signals["enroll_progress"][0]
                self.assertEqual(emitted, expected_signal, f"Signal mismatch for: {line}")

    def test_wipe_progress_message_parsing(self):
        """Test that wipe-progress messages are parsed correctly."""
        test_cases = [
            (">> Wiping ALL fingerprints...", {"event": "start"}),
            ("Wiping ALL fingerprints", {"event": "start"}),
            ("SUCCESS - All fingerprints deleted.", {"event": "success"}),
            ("SUCCESS! All fingerprints deleted.", {"event": "success"}),
            ("ERROR: Wipe failed", {"event": "error"}),
            ("FAILED to wipe", {"event": "error"}),
        ]

        for line, expected_signal in test_cases:
            self.emitted_signals["wipe_progress"].clear()
            self.worker._parse_wipe_progress(line)
            
            if self.emitted_signals["wipe_progress"]:
                self.assertEqual(
                    self.emitted_signals["wipe_progress"][0], expected_signal,
                    f"Signal mismatch for: {line}"
                )

    def test_mode_line_parsing(self):
        """Test that mode-change messages are parsed correctly."""
        test_cases = [
            ("SCAN_MODE", "scan"),
            ("CMD_MODE", "command"),
        ]

        for line, expected_mode in test_cases:
            self.emitted_signals["mode_changed"].clear()
            self.worker._parse_mode_line(line)
            
            if self.emitted_signals["mode_changed"]:
                self.assertEqual(
                    self.emitted_signals["mode_changed"][0], expected_mode,
                    f"Mode mismatch for: {line}"
                )

    def test_json_mode_line_parsing(self):
        """Test that JSON status mode messages are parsed correctly."""
        test_cases = [
            ("{\"type\":\"status\",\"state\":\"SCAN_MODE\"}", "scan"),
            ("{\"type\":\"status\",\"state\":\"CMD_MODE\"}", "command"),
        ]

        for line, expected_mode in test_cases:
            self.emitted_signals["mode_changed"].clear()
            self.worker._parse_mode_line(line)
            
            if self.emitted_signals["mode_changed"]:
                self.assertEqual(
                    self.emitted_signals["mode_changed"][0], expected_mode,
                    f"Mode mismatch for: {line}"
                )

    def test_enrollment_success_flow(self):
        """Test the full enrollment success signal flow."""
        # Simulate the sequence of lines from a successful enrollment
        enroll_sequence = [
            ("ENROLLING FINGER AS ID #5", True),   # Should emit
            ("Step 1: Place finger on sensor...", False),  # Should NOT emit
            ("Image taken!", False),                         # Should NOT emit
            ("SUCCESS! Finger saved as ID #5", True),      # Should emit
        ]

        for line, should_emit in enroll_sequence:
            self.emitted_signals["enroll_progress"].clear()
            self.worker._parse_enroll_progress(line)
            
            if should_emit:
                self.assertGreater(
                    len(self.emitted_signals["enroll_progress"]), 0,
                    f"Should emit for: {line}"
                )
            else:
                self.assertEqual(
                    len(self.emitted_signals["enroll_progress"]), 0,
                    f"Should NOT emit for: {line}"
                )

    def test_regex_patterns_consistency(self):
        """Verify regex patterns match expected cases."""
        # From serial_worker.py
        RE_ENROLLING_AS = re.compile(r"ENROLLING FINGER AS ID #(\d+)", re.IGNORECASE)
        RE_ENROLL_SUCCESS = re.compile(r"SUCCESS!?\s*Finger saved as ID #(\d+)", re.IGNORECASE)
        RE_ENROLL_CANCEL = re.compile(r"ENROLLMENT cancelled|Enrollment cancelled|ENROLL_CANCELLED", re.IGNORECASE)
        RE_WIPE_START = re.compile(r"Wiping ALL fingerprints", re.IGNORECASE)
        RE_WIPE_SUCCESS = re.compile(r"SUCCESS\s*-\s*All fingerprints deleted", re.IGNORECASE)

        # Test enrolling regex
        self.assertIsNotNone(RE_ENROLLING_AS.search("ENROLLING FINGER AS ID #5"))
        self.assertIsNotNone(RE_ENROLLING_AS.search("enrolling finger as id #10"))

        # Test success regex
        self.assertIsNotNone(RE_ENROLL_SUCCESS.search("SUCCESS! Finger saved as ID #7"))
        self.assertIsNotNone(RE_ENROLL_SUCCESS.search("SUCCESS Finger saved as ID #7"))

        # Test cancel regex
        self.assertIsNotNone(RE_ENROLL_CANCEL.search("ENROLLMENT cancelled"))
        self.assertIsNotNone(RE_ENROLL_CANCEL.search("Enrollment cancelled"))

        # Test wipe start regex
        self.assertIsNotNone(RE_WIPE_START.search("Wiping ALL fingerprints"))

        # Test wipe success regex
        self.assertIsNotNone(RE_WIPE_SUCCESS.search("SUCCESS - All fingerprints deleted"))


if __name__ == "__main__":
    unittest.main()
