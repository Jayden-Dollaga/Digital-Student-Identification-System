import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from core.attendance import AttendanceProcessor


class AttendanceProcessorTests(unittest.TestCase):
    def test_process_registered_scan_and_cooldown(self):
        logged = []

        def fake_log_attendance(fingerprint_id, confidence, status, now):
            logged.append((fingerprint_id, confidence, status, now))

        processor = AttendanceProcessor(cooldown_seconds=1, min_confidence=200, log_attendance_fn=fake_log_attendance)

        self.assertIsNone(processor.process_line("ID:1"))
        result = processor.process_line("CONFIDENCE:250")

        self.assertIsNotNone(result)
        self.assertEqual(result["fingerprint_id"], 1)
        self.assertEqual(result["confidence"], 250)
        self.assertEqual(result["status"], "GOOD MATCH")
        self.assertTrue(result["logged"])
        self.assertEqual(result["reason"], None)
        self.assertEqual(len(logged), 1)

        self.assertIsNone(processor.process_line("ID:1"))
        cooldown_result = processor.process_line("CONFIDENCE:250")
        self.assertIsNotNone(cooldown_result)
        self.assertFalse(cooldown_result["logged"])
        self.assertIn("Cooldown", cooldown_result["reason"])
        self.assertEqual(len(logged), 1)

    def test_process_unknown_scan_and_cooldown(self):
        logged = []

        def fake_log_attendance(fingerprint_id, confidence, status, now):
            logged.append((fingerprint_id, confidence, status, now))

        processor = AttendanceProcessor(cooldown_seconds=1, log_attendance_fn=fake_log_attendance)

        result = processor.process_line("UNKNOWN")
        self.assertIsNotNone(result)
        self.assertEqual(result["fingerprint_id"], 0)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertTrue(result["logged"])
        self.assertEqual(len(logged), 1)

        cooldown_result = processor.process_line("UNKNOWN")
        self.assertIsNotNone(cooldown_result)
        self.assertFalse(cooldown_result["logged"])
        self.assertEqual(len(logged), 1)

    def test_process_json_attendance_match(self):
        logged = []

        def fake_log_attendance(fingerprint_id, confidence, status, now):
            logged.append((fingerprint_id, confidence, status, now))

        processor = AttendanceProcessor(cooldown_seconds=1, min_confidence=200, log_attendance_fn=fake_log_attendance)

        result = processor.process_line('{"type":"attendance","event":"match","id":1,"confidence":250}')

        self.assertIsNotNone(result)
        self.assertEqual(result["fingerprint_id"], 1)
        self.assertEqual(result["confidence"], 250)
        self.assertEqual(result["status"], "GOOD MATCH")
        self.assertTrue(result["logged"])
        self.assertEqual(len(logged), 1)

    def test_reset_clears_state(self):
        logged = []

        def fake_log_attendance(fingerprint_id, confidence, status, now):
            logged.append((fingerprint_id, confidence, status, now))

        processor = AttendanceProcessor(cooldown_seconds=1, log_attendance_fn=fake_log_attendance)
        processor.process_line("ID:1")
        processor.process_line("CONFIDENCE:250")
        self.assertEqual(len(processor.last_scan), 1)
        self.assertEqual(len(logged), 1)

        processor.reset()
        self.assertEqual(processor.current_id, None)
        self.assertEqual(processor.last_scan, {})


if __name__ == "__main__":
    unittest.main()
