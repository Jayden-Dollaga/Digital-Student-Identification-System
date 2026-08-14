"""Tests for student input validation."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core.database import validate_student_input, add_student, update_student, init_database, clear_all_students


class TestStudentInputValidation:
    """Test student input validation."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test database."""
        init_database()
        clear_all_students()  # Clear students before each test
        yield
    
    def test_validate_fingerprint_id_too_low(self):
        """Fingerprint ID must be >= 1."""
        ok, msg = validate_student_input(0, "S001", "John Doe", "10", "A")
        assert not ok
        assert "1 and 127" in msg
    
    def test_validate_fingerprint_id_too_high(self):
        """Fingerprint ID must be <= 127."""
        ok, msg = validate_student_input(128, "S001", "John Doe", "10", "A")
        assert not ok
        assert "1 and 127" in msg
    
    def test_validate_fingerprint_id_valid(self):
        """Valid fingerprint IDs (1-127)."""
        for fid in [1, 64, 127]:
            ok, msg = validate_student_input(fid, "S001", "John Doe", "10", "A")
            assert ok, f"ID {fid} should be valid: {msg}"
    
    def test_validate_student_no_empty(self):
        """Student number is required."""
        ok, msg = validate_student_input(1, "", "John Doe", "10", "A")
        assert not ok
        assert "required" in msg.lower()
    
    def test_validate_student_no_too_long(self):
        """Student number has max length."""
        ok, msg = validate_student_input(1, "S" * 51, "John Doe", "10", "A")
        assert not ok
        assert "50 characters" in msg
    
    def test_validate_student_no_valid(self):
        """Valid student numbers."""
        for sno in ["S001", "2024-001", "student_01", "S-001"]:
            ok, msg = validate_student_input(1, sno, "John Doe", "10", "A")
            assert ok, f"Student No '{sno}' should be valid: {msg}"
    
    def test_validate_student_no_invalid_chars(self):
        """Student number rejects invalid characters."""
        ok, msg = validate_student_input(1, "S@001", "John Doe", "10", "A")
        assert not ok
        assert "invalid characters" in msg.lower()
    
    def test_validate_student_name_empty(self):
        """Student name is required."""
        ok, msg = validate_student_input(1, "S001", "", "10", "A")
        assert not ok
        assert "required" in msg.lower()
    
    def test_validate_student_name_too_long(self):
        """Student name has max length."""
        ok, msg = validate_student_input(1, "S001", "A" * 101, "10", "A")
        assert not ok
        assert "100 characters" in msg
    
    def test_validate_student_name_valid(self):
        """Valid student names."""
        for name in ["John Doe", "Mary-Jane", "O'Brien", "Jose Maria"]:
            ok, msg = validate_student_input(1, "S001", name, "10", "A")
            assert ok, f"Name '{name}' should be valid: {msg}"
    
    def test_validate_student_name_invalid_chars(self):
        """Student name rejects invalid characters."""
        ok, msg = validate_student_input(1, "S001", "John123", "10", "A")
        assert not ok
        assert "invalid characters" in msg.lower()
    
    def test_validate_grade_empty(self):
        """Grade is required."""
        ok, msg = validate_student_input(1, "S001", "John Doe", "", "A")
        assert not ok
        assert "required" in msg.lower()
    
    def test_validate_grade_valid(self):
        """Valid grades."""
        for grade in ["10", "10A", "10-A", "Grade-10", "X/Y"]:
            ok, msg = validate_student_input(1, "S001", "John Doe", grade, "A")
            assert ok, f"Grade '{grade}' should be valid: {msg}"
    
    def test_validate_section_empty(self):
        """Section is required."""
        ok, msg = validate_student_input(1, "S001", "John Doe", "10", "")
        assert not ok
        assert "required" in msg.lower()
    
    def test_validate_section_valid(self):
        """Valid sections."""
        for section in ["A", "A1", "A-1", "Class A"]:
            ok, msg = validate_student_input(1, "S001", "John Doe", "10", section)
            assert ok, f"Section '{section}' should be valid: {msg}"
    
    def test_add_student_with_invalid_input(self):
        """add_student rejects invalid input."""
        ok, msg = add_student(128, "S001", "John Doe", "10", "A")  # ID too high
        assert not ok
        assert "1 and 127" in msg
    
    def test_add_student_with_valid_input(self):
        """add_student accepts valid input."""
        ok, msg = add_student(1, "S001", "John Doe", "10", "A")
        assert ok, f"add_student failed: {msg}"
    
    def test_update_student_with_invalid_input(self):
        """update_student rejects invalid input."""
        # First add a student
        add_student(1, "S001", "John Doe", "10", "A")
        
        # Try to update with invalid name (with numbers)
        ok, msg = update_student(1, "S001", "John123", "10", "A")
        assert not ok
        assert "invalid characters" in msg.lower()
