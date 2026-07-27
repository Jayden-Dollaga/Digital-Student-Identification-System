import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from core.firmware_helper import discover_firmware_candidates, find_firmware_binary


def test_discover_firmware_candidates_prefers_bin(tmp_path):
    firmware_dir = tmp_path / "firmware" / "attendance"
    firmware_dir.mkdir(parents=True)
    expected = firmware_dir / "attendance.bin"
    expected.write_bytes(b"fake firmware")

    candidates = discover_firmware_candidates(project_root=tmp_path)

    assert expected in candidates
    assert find_firmware_binary(project_root=tmp_path) == expected
