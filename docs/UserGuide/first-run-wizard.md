# First-run Wizard

The first-run wizard is routed by `python/core/setup_wizard.py` and surfaced by the v3 frontend.

## Step order

The fixed order is:

1. **Password**
2. **Device**
3. **Schedule**
4. **Branding**

The password step is considered complete when a valid authentication record exists. The other steps use explicit settings flags so an interrupted wizard can resume.

## Step 1 — Password

Create the first administrator password.

Rules:

- minimum length: 8 characters,
- confirmation must match,
- password is hashed with PBKDF2-HMAC-SHA256,
- random 16-byte salt,
- 310,000 iterations.

The first-run method refuses to overwrite an existing administrator password.

## Step 2 — Device

The wizard can attempt to connect and validate the ESP32. It can also be skipped with the explicit “connect it later” choice.

Successful connection or explicit skip marks the device setup step complete.

## Step 3 — Schedule

Set:

- Time In,
- Time Out,
- early threshold,
- late threshold,
- absent threshold,
- recurring no-class weekdays.

The settings are persisted when the step completes.

## Step 4 — Branding

Set:

- school name,
- dark/light theme.

Completion persists the final wizard flag.

## Resuming after interruption

The next step is computed from current settings and whether a password exists. Closing the app does not require starting the wizard from the beginning.

The password step is never represented by a settings flag, because the password hash itself is the durable completion signal.

## After the wizard

When no step remains, the API loads the normal session state. The process starts with the active session role determined by the authentication/session logic, not by the stored `current_role` setting.
