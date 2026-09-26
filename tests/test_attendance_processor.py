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
        self.assertEqual(result["method"], "card")
        self.assertIn("encrypted", result["reason"].lower())
        self.assertEqual(len(logged), 1)

    def test_unreadable_card_preserves_firmware_reason(self):
        processor = AttendanceProcessor(log_attendance_fn=lambda *args: None)
        result = processor.process_line(
            '{"type":"attendance","event":"card_unreadable","uid":"04:F3:D8:19:45:02:89",'
            '"reason":"Ultralight is not supported."}'
        )

        self.assertEqual(result["method"], "card")
        self.assertEqual(result["uid"], "04:F3:D8:19:45:02:89")
        self.assertEqual(result["reason"], "Ultralight is not supported.")

    def test_card_payload_must_match_linked_student_and_uid(self):
        logged = []
        student_record = {
            "fingerprint_id": 7,
            "student_no": "STUDENT-01",
            "student_name": "Maria Santos",
            "grade": "12",
            "section": "A",
            "card_uid": "B0:6F:0B:55",
        }
        processor = AttendanceProcessor(
            cooldown_seconds=1,
            log_attendance_fn=lambda *args: logged.append(args),
            student_lookup_fn=lambda fingerprint_id: student_record if fingerprint_id == 7 else None,
        )
        payload = rfid_card.encrypt_student_card_payload(7, "STUDENT-01", "B0:6F:0B:55")

        result = processor.process_line(
            f'{{"type":"attendance","event":"card","uid":"B0:6F:0B:56","data_hex":"{payload}"}}'
        )

        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["method"], "card")
        self.assertIn("different UID", result["reason"])
        self.assertEqual(logged[0][0], 0)

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

        payload = rfid_card.encrypt_student_card_payload(7, "STUDENT-01", "B0:6F:0B:55")
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

        payload = rfid_card.encrypt_student_card_payload(11, "STUDENT-11", "AA:BB:CC:DD")
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

    def test_rfid_registration_commits_only_after_matching_verified_write(self):
        api = Api()
        api._rfid_session_active = True
        api._rfid_session_fingerprint_id = 7
        student = {"fingerprint_id": 7, "student_no": "STUDENT-07", "student_name": "Student"}
        payload_hex = "AB" * 48
        with patch.object(api.serial, "is_connected", return_value=True), \
             patch("gui_web.api.db.get_student", return_value=student), \
             patch("gui_web.api.db.get_student_by_card_uid", return_value=None), \
             patch("gui_web.api.encrypt_student_card_payload", return_value=payload_hex), \
             patch("gui_web.api.cmds.cmd_card_write_hex", return_value=True) as arm_write, \
             patch("gui_web.api.cmds.cmd_stop", return_value=True), \
             patch("gui_web.api.db.bind_student_card", return_value=(True, "Card registered.")) as bind_card, \
             patch.object(api, "_push") as push_mock:
            api._handle_rfid_session_card_event(
                '{"type":"attendance","event":"card","uid":"AA:BB:CC:DD","data_hex":"00"}'
            )

            bind_card.assert_not_called()
            arm_write.assert_called_once_with(api.serial, payload_hex)
            self.assertEqual(api._rfid_pending_uid, "AA:BB:CC:DD")

            api._handle_rfid_session_card_event(
                f'{{"type":"card_write","uid":"AA:BB:CC:DD","data_hex":"{payload_hex}","success":true}}'
            )

        bind_card.assert_called_once_with(7, "AA:BB:CC:DD")
        self.assertIsNone(api._rfid_pending_uid)
        saved_events = [
            call.args[1] for call in push_mock.call_args_list
            if call.args[0] == "scan_result" and call.args[1].get("event") == "saved"
        ]
        self.assertEqual(len(saved_events), 1)

    def test_failed_rfid_write_preserves_existing_link(self):
        api = Api()
        api._rfid_session_active = True
        api._rfid_session_fingerprint_id = 7
        api._rfid_pending_uid = "AA:BB:CC:DD"
        api._rfid_pending_fingerprint_id = 7
        api._rfid_pending_payload_hex = "AB" * 48
        with patch("gui_web.api.db.bind_student_card") as bind_card, patch.object(api, "_push") as push_mock:
            api._handle_rfid_session_card_event(
                '{"type":"card_write","uid":"AA:BB:CC:DD","data_hex":"0000","success":false}'
            )

        bind_card.assert_not_called()
        self.assertIsNone(api._rfid_pending_uid)
        self.assertEqual(push_mock.call_args.args[1]["event"], "error")

    def test_rfid_registration_is_rejected_while_attendance_scan_is_active(self):
        api = Api()
        api._scanning = True
        permissions.set_session_role("admin")

        with patch.object(api.serial, "is_connected", return_value=True), \
             patch.object(commands, "cmd_scan") as scan_mock:
            result = api.start_rfid_register_session(7)

        self.assertFalse(result["ok"])
        self.assertIn("stop attendance scanning", result["message"].lower())
        scan_mock.assert_not_called()

    def test_batch_rfid_erase_arms_one_tap_erase_without_attendance_logging(self):
        api = Api()
        permissions.set_session_role("admin")
        try:
            with patch.object(api.serial, "is_connected", return_value=True), \
                 patch.object(commands, "cmd_scan", return_value=True), \
                 patch.object(commands, "cmd_card_erase", return_value=True) as erase_mock, \
                 patch.object(api, "_push") as push_mock, \
                 patch.object(api.processor, "_log_attendance") as log_attendance_mock:
                result = api.start_batch_rfid_erase(False)
                self.assertTrue(result["ok"])

                erase_mock.assert_called_once_with(api.serial)
                log_attendance_mock.assert_not_called()

                handled = api._handle_rfid_session_card_event(
                    '{"type":"card_write","uid":"E1:F9:40:66","data_hex":"00000000000000000000000000000000","success":true}'
                )
                self.assertTrue(handled)
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
        payload = rfid_card.encrypt_student_card_payload(7, "STUDENT-07", "AA:BB:CC:DD")
        self.assertEqual(len(payload), 96)
        self.assertEqual(len(rfid_card.get_or_create_rfid_app_key()), 32)
        decoded = rfid_card.decrypt_student_card_payload(payload, "AA:BB:CC:DD")
        self.assertEqual(decoded, (7, "STUDENT-07"))
        self.assertIsNone(rfid_card.decrypt_student_card_payload(payload, "AA:BB:CC:DE"))

    def test_rfid_payload_tampering_and_overflow_fail_closed(self):
        payload = rfid_card.encrypt_student_card_payload(7, "STUDENT-07", "AA:BB:CC:DD")
        changed = ("0" if payload[-1] != "0" else "1")
        tampered = payload[:-1] + changed
        self.assertIsNone(rfid_card.decrypt_student_card_payload(tampered, "AA:BB:CC:DD"))
        with self.assertRaises(ValueError):
            rfid_card.encrypt_student_card_payload(7, "STUDENT-NUMBER-TOO-LONG", "AA:BB:CC:DD")

    def test_rfid_payload_wrong_key_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            with patch("settings_store.SETTINGS_FILE", settings_path):
                original = rfid_card.get_or_create_rfid_app_key()
                ciphertext = rfid_card.encrypt_student_card_payload(21, "STUDENT-21", "AA:BB:CC:DD")

                wrong_key = b"\x00" * 32
                with patch("core.rfid_card.get_or_create_rfid_app_key", return_value=wrong_key):
                    self.assertIsNone(rfid_card.decrypt_student_card_payload(ciphertext, "AA:BB:CC:DD"))

                self.assertEqual(rfid_card.decrypt_student_card_payload(ciphertext, "AA:BB:CC:DD"), (21, "STUDENT-21"))
                self.assertNotEqual(original.hex(), wrong_key.hex())

    def test_new_rfid_key_is_separate_from_legacy_xor_keys(self):
        from settings_store import load_settings, save_settings

        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            with patch("settings_store.SETTINGS_FILE", settings_path):
                settings = load_settings()
                legacy_key = bytes.fromhex("A1" * 16)
                settings["rfid_payload_key"] = legacy_key.hex().upper()
                settings["rfid_app_key_hex"] = legacy_key.hex().upper()
                save_settings(settings)

                new_key = rfid_card.get_or_create_rfid_app_key()

                self.assertEqual(len(new_key), 32)
                self.assertNotEqual(new_key, legacy_key)
                self.assertEqual(rfid_card.get_or_create_rfid_app_key(), new_key)

    def test_cmd_card_write_hex_uses_hex_payload_safe_format(self):
        permissions.set_session_role("admin")
        try:
            payload = "AB" * 48
            self.assertEqual(commands.cmd_card_write_hex(SimpleNamespace(send_command=lambda cmd: cmd), payload), f"CARD_WRITE_HEX:{payload}")
            self.assertFalse(commands.cmd_card_write_hex(SimpleNamespace(send_command=lambda cmd: cmd), "AB" * 47))
            self.assertFalse(commands.cmd_card_write(SimpleNamespace(send_command=lambda cmd: cmd), "JAYDEN-0001"))
        finally:
            permissions.set_session_role("guest")


if __name__ == "__main__":
    unittest.main()
