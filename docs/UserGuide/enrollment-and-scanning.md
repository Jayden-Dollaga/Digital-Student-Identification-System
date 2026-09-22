# Enrollment and Scanning

This document records the actual enrollment and scan behavior in the current app.

## Key rule

The system only stores a student row after the device-side enrollment succeeds, and a fingerprint ID is only considered valid when it maps to the sensor state appropriately.

## Enrollment behavior

The enrollment flow includes:

- validating the student metadata,
- requesting the device to begin enroll mode,
- waiting for the AS608 to complete the fingerprint capture stages,
- writing the student record into `students`,
- preserving the fingerprint ID mapping used for later recognition.

## Scanning behavior

When the device reports a match:

- the Python parser extracts the fingerprint ID and confidence,
- `AttendanceProcessor` checks whether the action is under cooldown,
- valid scanning events are written into `attendance`,
- the frontend receives a refreshed event or dashboard update.

## Unknown or low-confidence events

- unknown scans are logged as unknown events according to the current processor behavior,
- low-confidence values are filtered according to the configured minimum threshold,
- repeated scans may be suppressed by cooldown logic.

## Delete and wipe behavior

Delete and wipe actions are device operations and can also have DB-side effects. These are privileged actions and are subject to current role and permission checks.
