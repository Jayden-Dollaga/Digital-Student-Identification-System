#!/usr/bin/env python3
"""
Regression tests for student input validation fix.
Verifies that legitimate punctuation is preserved in student names and sections.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

import pytest
from core.database import validate_student_input, get_student_field_feedback


class TestStudentInputValidationRegressions:
    """Test cases for punctuation preservation regression fix."""
    
    def test_name_with_comma_and_period(self):
        """Full names with commas and periods should be accepted."""
        is_valid, error_msg = validate_student_input(
            fingerprint_id=1,
            student_no="2024001",
            student_name="Santos, Maria-Jane L.",
            grade="12",
            section="CSS-12-1"
        )
        assert is_valid, f"Should accept name with comma and period. Error: {error_msg}"
    
    def test_name_with_multiple_commas(self):
        """Names with multiple commas should be accepted."""
        is_valid, error_msg = validate_student_input(
            fingerprint_id=2,
            student_no="2024002",
            student_name="Dollaga, Jayden Ralfh B.",
            grade="11",
            section="STEM-11-2"
        )
        assert is_valid, f"Should accept name with multiple punctuation marks. Error: {error_msg}"
    
    def test_name_with_apostrophe_and_comma(self):
        """Names with apostrophes and commas should be accepted."""
        is_valid, error_msg = validate_student_input(
            fingerprint_id=3,
            student_no="2024003",
            student_name="O'Connor, Liam J.",
            grade="10",
            section="ICT-10-1"
        )
        assert is_valid, f"Should accept name with apostrophe and comma. Error: {error_msg}"
    
    def test_name_with_unicode_letters(self):
        """Names with Unicode letters should be accepted."""
        names = [
            "José Santos",
            "García López",
            "François Dubois",
            "Müller Schmidt",
            "Søren Jensen",
            "Łukasz Nowak",
            "Chloë Martin",
        ]
        for index, name in enumerate(names, start=4):
            is_valid, error_msg = validate_student_input(
                fingerprint_id=index,
                student_no=f"202400{index}",
                student_name=name,
                grade="9",
                section="GEN-9-3"
            )
            assert is_valid, f"Should accept Unicode name '{name}'. Error: {error_msg}"

    def test_unicode_names_round_trip_in_validation_feedback(self):
        """Unicode names should remain unchanged in validation feedback as well as in storage."""
        names = [
            "José Santos",
            "García López",
            "François Dubois",
            "Müller Schmidt",
            "Søren Jensen",
            "Łukasz Nowak",
            "Chloë Martin",
        ]
        for name in names:
            feedback = get_student_field_feedback(1, "2024001", name, "12", "CSS-12-1")
            result = feedback["student_name"]
            assert result.valid, f"{name} should be valid: {result.message}"
            assert name == name.strip(), f"{name} should not be silently altered"
    
    def test_section_with_hyphens(self):
        """Section IDs with hyphens should be accepted."""
        test_cases = [
            ("CSS-1", "Single hyphen section"),
            ("CSS-12-1", "Multiple hyphens in section"),
            ("STEM-12-1", "STEM class section"),
            ("ICT-11-2", "ICT class section"),
            ("A-1-1", "Single letter prefix"),
        ]
        
        for section, description in test_cases:
            is_valid, error_msg = validate_student_input(
                fingerprint_id=5,
                student_no="2024005",
                student_name="Test Student",
                grade="10",
                section=section
            )
            assert is_valid, f"{description} failed: {error_msg}"
    
    def test_student_no_with_special_chars(self):
        """Student numbers with valid special characters should be accepted."""
        test_cases = [
            "2024-001",  # with hyphen
            "2024.001",  # with period
            "2024_001",  # with underscore
            "SY2024-001",  # prefix with hyphen
        ]
        
        for student_no in test_cases:
            is_valid, error_msg = validate_student_input(
                fingerprint_id=6,
                student_no=student_no,
                student_name="Test Student",
                grade="10",
                section="CSS-10-1"
            )
            assert is_valid, f"Student number {student_no} should be valid. Error: {error_msg}"
    
    def test_reject_control_characters(self):
        """Control characters should still be rejected."""
        is_valid, error_msg = validate_student_input(
            fingerprint_id=7,
            student_no="2024007",
            student_name="Test\nNewline",  # Newline character
            grade="10",
            section="CSS-10-1"
        )
        assert not is_valid, "Should reject names with control characters"
    
    def test_reject_excessive_length(self):
        """Names longer than 100 characters should be rejected."""
        long_name = "A" * 101
        is_valid, error_msg = validate_student_input(
            fingerprint_id=8,
            student_no="2024008",
            student_name=long_name,
            grade="10",
            section="CSS-10-1"
        )
        assert not is_valid, "Should reject names longer than 100 characters"
    
    def test_reject_null_bytes(self):
        """Null bytes should be rejected."""
        is_valid, error_msg = validate_student_input(
            fingerprint_id=9,
            student_no="2024009",
            student_name="Test\x00Null",
            grade="10",
            section="CSS-10-1"
        )
        assert not is_valid, "Should reject names with null bytes"
    
    def test_empty_name_rejected(self):
        """Empty student name should be rejected."""
        is_valid, error_msg = validate_student_input(
            fingerprint_id=10,
            student_no="2024010",
            student_name="",
            grade="10",
            section="CSS-10-1"
        )
        assert not is_valid, "Should reject empty student name"
    
    def test_whitespace_only_name_rejected(self):
        """Whitespace-only names should be rejected."""
        is_valid, error_msg = validate_student_input(
            fingerprint_id=11,
            student_no="2024011",
            student_name="   ",
            grade="10",
            section="CSS-10-1"
        )
        assert not is_valid, "Should reject whitespace-only student name"

    def test_live_validation_feedback_preserves_valid_name(self):
        """Valid names with punctuation remain unchanged and marked valid."""
        names = [
            "Dollaga, Jayden Ralfh B.",
            "Santos, Maria-Jane L.",
            "O'Connor, Liam J.",
            "José Santos",
        ]
        for name in names:
            feedback = get_student_field_feedback(1, "120001001", name, "12", "CSS-12-1")
            result = feedback["student_name"]
            assert result.valid, f"'{name}' should be valid: {result.message}"
            assert name == name.strip(), f"'{name}' should not be silently modified"

    def test_live_validation_feedback_reports_unsupported_character(self):
        """The warning layer reports the offending symbol without exposing regex internals."""
        feedback = get_student_field_feedback(1, "120001001", "Juan @Dela Cruz", "12", "CSS-12-1")
        result = feedback["student_name"]
        assert not result.valid
        assert "Unsupported character" in result.message
        assert "@" in result.message
        assert "regex" not in result.message.lower()

    def test_live_validation_feedback_accepts_section_formats(self):
        """Valid section formats are accepted without rewriting them."""
        for section in ["CSS-1", "CSS-12-1", "STEM-12-1", "ICT-11-2"]:
            feedback = get_student_field_feedback(1, "120001001", "Dollaga, Jayden Ralfh B.", "12", section)
            result = feedback["section"]
            assert result.valid, f"'{section}' should be valid: {result.message}"
            assert section == section.strip()
    
    def test_complex_real_world_names(self):
        """Test complex real-world names with various punctuation."""
        complex_names = [
            "de la Cruz, Maria Jose M.",
            "van der Berg, Johann P.",
            "O'Shaughnessy-Murphy, Brigid E.",
            "Smith, Mary-Ann. K.",
            "St. James, Michael T.",
        ]
        
        for name in complex_names:
            is_valid, error_msg = validate_student_input(
                fingerprint_id=12,
                student_no="2024012",
                student_name=name,
                grade="10",
                section="CSS-10-1"
            )
            assert is_valid, f"Complex name '{name}' should be valid. Error: {error_msg}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
