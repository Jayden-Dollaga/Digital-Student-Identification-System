import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from gui.layout_utils import resolve_dialog_size, resolve_window_size, resolve_sidebar_width, scale_value


def test_resolve_window_size_uses_screen_bounds():
    width, height = resolve_window_size(1280, 720)
    assert width <= 1280 - 40
    assert height <= 720 - 40
    assert width >= 960
    assert height >= 600


def test_resolve_dialog_size_stays_within_screen():
    width, height = resolve_dialog_size(1280, 720, default_width=760, default_height=520)
    assert width <= 1280 - 40
    assert height <= 720 - 40


def test_sidebar_width_scales_for_small_screens():
    width = resolve_sidebar_width(1024, 768)
    assert width <= 320
    assert width >= 240


def test_scale_value_clamps_to_bounds():
    assert scale_value(18, 0.8, minimum=12, maximum=16) == 14
    assert scale_value(10, 1.2, minimum=12, maximum=20) == 12
