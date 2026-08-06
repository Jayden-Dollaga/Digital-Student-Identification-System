# ESP32_Fingerprint_AllInOne Firmware Explanation

This document explains the firmware in `firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino`.
It covers the main code sections and describes what each part does.

## Overview

The firmware runs on an ESP32 and communicates with an AS608 fingerprint sensor over a second hardware serial port.
It supports:

- command mode for enrollment, deletion, listing, and wiping fingerprints
- scan mode for attendance scanning
- LED status animations on the onboard D2 LED
- structured JSON status and attendance output on the primary USB serial port

## Key definitions and constants

- `FINGERPRINT_RX`, `FINGERPRINT_TX`: ESP32 pins connected to the sensor's TX and RX wires.
- `LED_PIN`: onboard LED pin used for status output.
- timing constants such as `SCAN_COOLDOWN`, `BOOT_PULSE_PERIOD_MS`, and `SUCCESS_TOTAL_MS` control LED animation timing.
- `MIN_CONFIDENCE`: minimum fingerprint confidence value required to accept a match.

## LED state management

The firmware defines an `enum LedState` with states like `LED_BOOTING`, `LED_READY`, `LED_SCAN`, `LED_SUCCESS`, `LED_ENROLL`, `LED_ERROR`, and more.

A priority system determines whether a temporary LED state can override the current state, and whether the code should restore the previous state afterward.

### LED helpers

- `ledBrightness(value)`: sets the LED duty cycle. On ESP32 this uses PWM; on non-ESP32 boards it toggles the LED fully on or off.
- `ledOff()`: turns the LED off.
- `getPriorityForState(state)`: returns a numeric priority for each LED state.
- `requestLedState(state, temporary)`: requests a new LED mode, optionally as a temporary alert.
- `restoreLedStateIfNeeded()`: restores the prior LED mode after a temporary state expires.

### LED update loop

`updateLed()` runs continuously and updates the LED effect based on the current state:

- `LED_BOOTING`: smooth pulse fade in/out while firmware boots.
- `LED_READY` / `LED_HOST_CONNECTED`: short periodic blink to show idle readiness.
- `LED_SCAN`: faster pulsing for attendance scan mode.
- `LED_ENROLL`: repeated flash pattern while enrollment is in progress.
- `LED_SUCCESS`: solid ON for a short interval, then restore the previous state.
- `LED_ERROR` / `LED_DB_ERROR`: rapid blinking for a limited time, then restore.
- `LED_COMMUNICATION_ERROR`: long on/off blink pattern.
- `LED_HOST_DISCONNECTED`, `LED_SLEEP`: LED off.

## JSON output and host status parsing

The firmware emits JSON messages over serial for host integration.

### Emitters

- `emitJsonStatus(state)`: sends `{"type":"status","state":"..."}`.
- `emitJsonAttendanceMatch(id, confidence)`: sends attendance matches with ID and confidence.
- `emitJsonAttendanceUnknown()`: sends `{"type":"attendance","event":"unknown"}`.
- `emitJsonAttendanceLowConfidence(confidence)`: sends low-confidence events.

### Parsing host JSON input

- `parseJsonStringField(json, field)` is a lightweight parser that extracts a quoted string field from an incoming JSON-like serial payload.
- `handleHostStatus(status)` maps host status strings like `HOST_CONNECTED`, `HOST_DISCONNECTED`, `DB_ERROR`, `FIRMWARE`, and `READY` to LED states.

## Firmware setup

`setup()` performs the startup sequence:

1. Initialize the LED manager and attach PWM to the onboard LED.
2. Open the main USB serial port at 115200 baud.
3. Run the boot LED animation for one second.
4. Print device information and firmware metadata.
5. Initialize the fingerprint sensor serial port at 57600 baud.
6. Verify the sensor is present; if verification fails the firmware enters an error loop.
7. Print the stored fingerprint count, show help text, and emit a `READY` status message.

## Main loop behavior

`loop()` is the firmware heartbeat:

- calls `updateLed()` constantly so the LED animations keep running.
- processes any previously queued command from an interrupted enrollment.
- reads serial commands from the host and passes them to `handleCommand(input)`.
- when scan mode is active, calls `scanFinger()` repeatedly.

## Command handling

`handleCommand(input)` accepts serial commands and performs the following actions:

- `ID?`: prints device identity and firmware metadata.
- `SCAN`: enters attendance scanning mode, sets the LED, prints user guidance, and emits `SCAN_MODE`.
- `STOP`: leaves scan mode, returns to ready state, prints help, and emits `CMD_MODE`.
- `LIST`: shows the number of stored fingerprints.
- `WIPE`: deletes all stored fingerprints.
- `ENROLL`: enrolls a fingerprint into the next available ID.
- `ENROLL:<id>`: enrolls a fingerprint into the specified ID.
- `DELETE:<id>`: removes a stored fingerprint by ID.
- `STATUS:<state>`: changes the LED state according to the host status string.
- JSON input beginning with `{`: reads status messages and updates the LED.
- any other input: prints help text.

## Enrollment helpers

- `fingerprintExists(id)`: checks whether a fingerprint template is already stored at `id`.
- `findNextAvailableId()`: searches IDs 1 to 127 for the next free fingerprint slot.
- `checkEnrollmentCancel()`: during enrollment, polls serial input so the user can cancel or queue a new command.

If enrollment is cancelled by `STOP` or a new command, the code stores the pending command and returns to the command loop.

## Enrollment process

`enrollFinger(id)` performs a two-step enrollment process:

1. Prompt the user to place a finger and wait until `finger.getImage()` returns `FINGERPRINT_OK`.
2. Convert the first image to template slot 1 with `image2Tz(1)`.
3. Wait for the finger to be removed.
4. Prompt for the same finger again and capture the second image.
5. Convert the second image to template slot 2 with `image2Tz(2)`.
6. Call `finger.createModel()` to combine the two captures.
   - if the captures do not match, it shows an error and asks the user to retry.
7. Call `finger.storeModel(id)` to save the fingerprint template to the specified ID.
   - on success, the firmware flashes success and reports the stored count.
   - on failure, it flashes an error.

## Scan mode

`scanFinger()` handles attendance scanning while `scanMode` is true:

- captures an image from the sensor.
- converts the image into a template.
- searches the fingerprint database.
- if a match is found and confidence is above the threshold, emits a JSON `match` event and flashes success.
- if the match confidence is too low, emits a `low_confidence` event.
- if there is no match, emits an `unknown` event.
- after each scan it delays briefly to avoid repeated rapid events.

## Help text

`printHelp()` prints the available serial commands and usage examples so the user can control the firmware from the serial monitor or host application.

## Summary

The firmware is designed as an all-in-one sketch for the ESP32 with the AS608 fingerprint sensor. It provides:

- host command support for enroll/delete/list/wipe/scan
- a scan mode that emits structured JSON attendance events
- LED feedback for status, enrollment, success, errors, and scan activity
- a lightweight JSON parser for host-driven LED status updates

This document should help developers understand the firmware structure and how the main code sections work together.
