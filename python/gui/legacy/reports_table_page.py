"""Compatibility surface for the archived reports page."""

from core.database import get_daily_attendance_summary


class ReportsPage:
    """Non-UI compatibility stub for archived imports."""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


__all__ = ["ReportsPage", "get_daily_attendance_summary"]
