from __future__ import annotations

from typing import Tuple


def scale_value(value: int | float, scale: float, minimum: int | float | None = None, maximum: int | float | None = None) -> int | float:
    """Scale a value and clamp it to a sensible range."""
    scaled = value * scale
    if minimum is not None:
        scaled = max(scaled, minimum)
    if maximum is not None:
        scaled = min(scaled, maximum)
    return int(scaled)


def resolve_window_size(screen_width: int, screen_height: int) -> Tuple[int, int]:
    """Return a window size that fits the current screen while keeping the app usable."""
    max_width = max(960, min(1440, screen_width - 40))
    max_height = max(600, min(900, screen_height - 60))

    width = min(max_width, 1440)
    height = min(max_height, 900)

    if width < 1100:
        width = max(960, width)
    if height < 700:
        height = max(600, height)

    return width, height


def resolve_dialog_size(screen_width: int, screen_height: int, default_width: int, default_height: int) -> Tuple[int, int]:
    """Return dialog dimensions that fit the screen and scale down on smaller displays."""
    max_width = max(360, min(default_width, screen_width - 40))
    max_height = max(320, min(default_height, screen_height - 60))
    return max_width, max_height


def resolve_sidebar_width(screen_width: int, screen_height: int) -> int:
    """Choose a sidebar width based on the available screen size."""
    if screen_width < 1200:
        return 260
    if screen_width < 1600:
        return 300
    return 320


def get_scaling_factor(screen_width: int, screen_height: int) -> float:
    """Return a scaling factor suitable for the current display size."""
    base = min(screen_width / 1440, screen_height / 900)
    return max(0.85, min(1.15, base))
