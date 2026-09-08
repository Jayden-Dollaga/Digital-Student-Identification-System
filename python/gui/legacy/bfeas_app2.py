"""Compatibility entry point for the archived legacy GUI.

The maintained application is the V3 web UI. This module remains importable
for older launchers and test harnesses without executing archived GUI code.
"""


def main() -> None:
    """Keep the historical entry point callable without starting a legacy UI."""
    return None


if __name__ == "__main__":
    main()
