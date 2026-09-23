import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "python"
import pytest

pytestmark = pytest.mark.unit
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from core import database as db
from core import permissions
from core.attendance import AttendanceProcessor
from core import commands
from core import rfid_card
from gui_web.api import Api


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

    def test_process_json_attendance_match_with_bom_and_whitespace(self):
        logged = []

        def fake_log_attendance(fingerprint_id, confidence, status, now):
            logged.append((fingerprint_id, confidence, status, now))

        processor = AttendanceProcessor(cooldown_seconds=1, min_confidence=200, log_attendance_fn=fake_log_attendance)

        line = '\ufeff  {"type":"attendance","event":"match","id":7,"confidence":240}  \r\n'
        result = processor.process_line(line)

        self.assertIsNotNone(result)
        self.assertEqual(result["fingerprint_id"], 7)
        self.assertEqual(result["confidence"], 240)
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

    def test_card_match_uses_card_uid_resolution(self):
        logged = []
        student_record = {
            "fingerprint_id": 7,
            "student_no": "STUDENT-01",
            "student_name": "Maria Santos",
            "grade": "12",
            "section": "A",
            "card_uid": "B0:6F:0B:55",
        }

        def fake_log_attendance(fingerprint_id, confidence, status, now):
            logged.append((fingerprint_id, confidence, status, now))

        processor = AttendanceProcessor(
            cooldown_seconds=1,
            min_confidence=200,
            log_attendance_fn=fake_log_attendance,
            student_lookup_fn=lambda fingerprint_id: student_record if fingerprint_id == 7 else None,
            all_students_fn=lambda: [student_record],
        )

        payload = rfid_card.encrypt_student_card_payload(7, "STUDENT-01")
        result = processor.process_line(f'{{"type":"attendance","event":"card","uid":"B0:6F:0B:55","data_hex":"{payload}"}}')
        self.assertIsNotNone(result)
        self.assertEqual(result["fingerprint_id"], 7)
        self.assertEqual(result["method"], "card")
        self.assertEqual(result["status"], "GOOD MATCH")
        self.assertTrue(result["logged"])
        self.assertEqual(len(logged), 1)

    def test_unknown_card_is_logged_as_unknown_without_crashing(self):
        logged = []

        def fake_log_attendance(fingerprint_id, confidence, status, now):
            logged.append((fingerprint_id, confidence, status, now))

        processor = AttendanceProcessor(cooldown_seconds=1, log_attendance_fn=fake_log_attendance)
        result = processor.process_line('{"type":"attendance","event":"card","uid":"EE:EE:EE:EE","data":"NOT-FOUND"}')

        self.assertIsNotNone(result)
        self.assertEqual(result["fingerprint_id"], 0)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertTrue(result["logged"])
        self.assertEqual(len(logged), 1)

    def test_card_event_accepts_data_hex_payload(self):
        student_record = {
            "fingerprint_id": 11,
            "student_no": "STUDENT-11",
            "student_name": "Ellie Kim",
            "grade": "12",
            "section": "A",
            "card_uid": "AA:BB:CC:DD",
        }

        processor = AttendanceProcessor(
            cooldown_seconds=1,
            min_confidence=200,
            log_attendance_fn=lambda *args, **kwargs: None,
            student_lookup_fn=lambda fingerprint_id: student_record if fingerprint_id == 11 else None,
            all_students_fn=lambda: [student_record],
        )

        payload = rfid_card.encrypt_student_card_payload(11, "STUDENT-11")
        result = processor.process_line(f'{{"type":"attendance","event":"card","uid":"AA:BB:CC:DD","data_hex":"{payload}"}}')

        self.assertIsNotNone(result)
        self.assertEqual(result["fingerprint_id"], 11)
        self.assertEqual(result["method"], "card")
        self.assertEqual(result["status"], "GOOD MATCH")

    def test_active_rfid_register_session_skips_attendance_logging(self):
        api = Api()
        api._rfid_session_active = True
        api._rfid_session_was_scanning = False
        payload = '{"type":"attendance","event":"card","uid":"AA:BB:CC:DD","data":"STUDENT-11"}'

        with patch.object(api.processor, "_log_attendance") as log_attendance_mock, patch.object(api, "_push") as push_mock:
            api._handle_rfid_session_card_event(payload)

        log_attendance_mock.assert_not_called()
        push_mock.assert_called_once()

    def test_batch_rfid_erase_arms_zero_payload_without_attendance_logging(self):
        api = Api()
        permissions.set_session_role("admin")
        try:
            with patch.object(api.serial, "is_connected", return_value=True), \
                 patch.object(commands, "cmd_scan", return_value=True), \
                 patch.object(commands, "cmd_card_write_hex", return_value=True) as write_mock, \
                 patch.object(api, "_push") as push_mock, \
                 patch.object(api.processor, "_log_attendance") as log_attendance_mock:
                result = api.start_batch_rfid_erase(False)
                self.assertTrue(result["ok"])

                handled = api._handle_rfid_session_card_event(
                    '{"type":"attendance","event":"card","uid":"E1:F9:40:66","data_hex":"AABB"}'
                )

                self.assertTrue(handled)
                write_mock.assert_called_once_with(api.serial, "0" * 32)
                log_attendance_mock.assert_not_called()
                self.assertEqual(push_mock.call_args[0][0], "scan_result")

                api._handle_rfid_session_card_event(
                    '{"type":"card_write","uid":"E1:F9:40:66","data_hex":"00000000000000000000000000000000","success":true}'
                )
                self.assertEqual(api._batch_rfid_erase_count, 1)
                api.stop_batch_rfid_erase()
        finally:
            permissions.set_session_role("guest")

    def test_card_cooldown_blocks_same_student_from_double_logging(self):
        logged = []
        student_record = {
            "fingerprint_id": 9,
            "student_no": "STUDENT-02",
            "student_name": "James Lee",
            "grade": "11",
            "section": "B",
            "card_uid": "AA:BB:CC:DD",
        }

        def fake_log_attendance(fingerprint_id, confidence, status, now):
            logged.append((fingerprint_id, confidence, status, now))

        processor = AttendanceProcessor(
            cooldown_seconds=1,
            min_confidence=200,
            log_attendance_fn=fake_log_attendance,
            student_lookup_fn=lambda fingerprint_id: student_record if fingerprint_id == 9 else None,
            all_students_fn=lambda: [student_record],
        )

        first = processor.process_line('{"type":"attendance","event":"match","id":9,"confidence":250}')
        second = processor.process_line('{"type":"attendance","event":"card","uid":"AA:BB:CC:DD","data_hex":"not-a-valid-payload"}')

        self.assertIsNotNone(first)
        self.assertTrue(first["logged"])
        self.assertIsNotNone(second)
        self.assertFalse(second["logged"])
        self.assertEqual(len(logged), 1)

    def test_bind_student_card_rejects_claimed_uid(self):
        with patch.object(db, "DB_PATH", str(Path(__file__).resolve().parent / "tmp_card_claim_test.db")):
            db.init_database()
            db.register_student(1, "STUDENT-01", "Maria Santos", "11", "A")
            db.register_student(2, "STUDENT-02", "Ben Reyes", "12", "B")

            ok, message = db.bind_student_card(1, "B0:6F:0B:55")
            self.assertTrue(ok)
            ok, message = db.bind_student_card(2, "B0:6F:0B:55")
            self.assertFalse(ok)
            self.assertIn("already registered", message.lower())

            db.clear_student_card(1)

    def test_rfid_payload_round_trip_uses_app_key(self):
        payload = rfid_card.encrypt_student_card_payload(7, "STUDENT-07")
        self.assertEqual(len(payload), 32)
        decoded = rfid_card.decrypt_student_card_payload(payload)
        self.assertEqual(decoded, (7, "STUDENT-07"))

    def test_rfid_payload_wrong_key_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            with patch("settings_store.SETTINGS_FILE", settings_path):
                original = rfid_card.get_or_create_rfid_app_key()
                ciphertext = rfid_card.encrypt_student_card_payload(21, "STUDENT-21")

                wrong_key = b"\x00" * 16
                with patch("core.rfid_card.get_or_create_rfid_app_key", return_value=wrong_key):
                    self.assertIsNone(rfid_card.decrypt_student_card_payload(ciphertext))

                self.assertEqual(rfid_card.decrypt_student_card_payload(ciphertext), (21, "STUDENT-21"))
                self.assertNotEqual(original.hex(), wrong_key.hex())

    def test_cmd_card_write_hex_uses_hex_payload_safe_format(self):
        permissions.set_session_role("admin")
        try:
            self.assertEqual(commands.cmd_card_write_hex(SimpleNamespace(send_command=lambda cmd: cmd), "aBcD"), "CARD_WRITE_HEX:aBcD")
            self.assertFalse(commands.cmd_card_write_hex(SimpleNamespace(send_command=lambda cmd: cmd), "ABC"))
            self.assertFalse(commands.cmd_card_write(SimpleNamespace(send_command=lambda cmd: cmd), "JAYDEN-0001"))
        finally:
            permissions.set_session_role("guest")


if __name__ == "__main__":
    unittest.main()
