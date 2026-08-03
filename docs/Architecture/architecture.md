# Architecture

The system is split into four cooperating layers:

1. Firmware layer: the ESP32 sketch reads fingerprint data and responds to serial commands.
2. Communication layer: the Python serial handler manages ports, reads, reconnect behavior, and device-state awareness.
3. Application logic layer: the attendance processor interprets scan results, applies cooldown and confidence rules, and returns structured outcomes for the rest of the app.
4. Presentation and persistence layers: the GUI handles user interaction while the database layer stores students, attendance records, reports, and backup data.

This organization keeps the codebase easier to maintain and makes future enhancements such as richer reporting, more robust reconnect logic, or additional device integrations simpler to add.
