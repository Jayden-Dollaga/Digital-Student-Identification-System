# V2 parity reference

This directory preserves a source snapshot of the proven V2 Qt implementation
next to the active V3 web implementation. It is intentionally reference-only:
V3 does not import or execute these Qt modules at runtime.

Use it when comparing workflow contracts, serial event handling, enrollment,
delete, wipe, settings, and shutdown behavior. Active V3 code remains in
`python/gui_web/api.py` and `python/gui_web/web/`.
