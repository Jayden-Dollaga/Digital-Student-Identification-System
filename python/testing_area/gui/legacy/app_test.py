"""Compatibility wrapper for the current GUI entry point."""

from gui.app import FingerprintApp, main

__all__ = ["FingerprintApp", "main"]


if __name__ == "__main__":
    main()
