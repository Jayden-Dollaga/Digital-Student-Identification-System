/************************************************************************************
 *  AS608 Fingerprint - All-in-One Sketch
 *  ESP32 WROOM-32 with Screw Terminal Shield
 *
 *  Replaces all 4 Phase 1 sketches with a single file.
 *  No need to re-upload when switching between enrolling and scanning.
 *
 *  Wiring (confirmed working):
 *    Sensor V+ (purple) -> Shield V terminal
 *    Sensor GND (blue)  -> Shield G terminal
 *    Sensor TX (orange) -> Shield S terminal, D14 row  <- ESP32 RX
 *    Sensor RX (white)  -> Shield S terminal, D27 row  <- ESP32 TX
 *
 *  ── COMMANDS (type in Serial Monitor, line ending = Newline) ──
 *
 *    ENROLL        Enroll a new finger using the next free ID
 *    ENROLL:1      Enroll a new finger as ID 1
 *    ENROLL:5      Enroll a new finger as ID 5
 *    DELETE:1      Delete finger ID 1
 *    WIPE          Delete ALL stored fingerprints
 *    LIST          Show how many fingerprints are stored
 *    SCAN          Switch to attendance scan mode
 *    STOP          Stop scanning, go back to command mode
 *
 *  ── TYPICAL WORKFLOW FOR A CLASS OF 30 ──
 *
 *    1. Upload this sketch once, never touch it again
 *    2. Open Serial Monitor at 115200, line ending = Newline
 *    3. Type ENROLL:1  -> scan student 1 finger twice -> saved
 *    4. Type ENROLL:2  -> scan student 2 finger twice -> saved
 *    5. Repeat up to ENROLL:30
 *    6. Type SCAN      -> now reading attendance, Python can connect
 *    7. Type STOP      -> go back to command mode anytime
 *
 *  ── SERIAL OUTPUT FORMAT (what Python reads in SCAN mode) ──
 *
 *    READY           System booted
 *    ID:1            Matched fingerprint ID
 *    CONFIDENCE:223  Match confidence score
 *    UNKNOWN         Finger not recognized
 *    SCAN_MODE       Entered scan mode
 *    CMD_MODE        Entered command mode
 *
 *  The firmware now also emits structured JSON payloads for status and
 *  attendance events, e.g.:
 *    {"type":"status","state":"SCAN_MODE"}
 *    {"type":"attendance","event":"match","id":1,"confidence":223}
 ************************************************************************************/

#include <Adafruit_Fingerprint.h>
#include <HardwareSerial.h>

#define FINGERPRINT_RX        14    // orange wire (sensor TX) connects here
#define FINGERPRINT_TX        27    // white wire  (sensor RX) connects here
#define LED_PIN               2     // onboard D2 LED on ESP32
#define LED_PWM_CHANNEL       0
#define LED_PWM_FREQUENCY     5000
#define LED_PWM_RESOLUTION    8
#define LED_MAX_BRIGHTNESS    255
#define MIN_CONFIDENCE        50    // minimum confidence to accept a match
#define SCAN_COOLDOWN         2000  // ms to wait after a scan before scanning again

const unsigned long BOOT_PULSE_PERIOD_MS = 2000;
const unsigned long SUCCESS_TOTAL_MS = 2500;
const unsigned long ERROR_BLINK_MS = 70;
const unsigned long ERROR_TOTAL_MS = 5000;
const unsigned long READY_ON_MS = 500;
const unsigned long READY_PERIOD_MS = 2000;
const unsigned long SCAN_PULSE_MS = 100;
const unsigned long ENROLL_ON_MS = 100;
const unsigned long ENROLL_OFF_MS = 100;
const unsigned long ENROLL_COUNT = 5;
const unsigned long ENROLL_END_OFF_MS = 700;
const unsigned long FIRMWARE_BLINK_MS = 500;
const unsigned long COMM_ERROR_ON_MS = 700;
const unsigned long COMM_ERROR_OFF_MS = 200;

HardwareSerial mySerial(2);
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);

enum LedState {
  LED_BOOTING,
  LED_READY,
  LED_SCAN,
  LED_SUCCESS,
  LED_ENROLL,
  LED_FIRMWARE,
  LED_ERROR,
  LED_DB_ERROR,
  LED_COMMUNICATION_ERROR,
  LED_HOST_CONNECTED,
  LED_HOST_DISCONNECTED,
  LED_SLEEP
};

const char DEVICE_IDENTIFIER[] = "Fingerprint Attendance";
const char DEVICE_BOARD[] = "ESP32";
const char DEVICE_FIRMWARE[] = "1.0";
const char DEVICE_SENSOR[] = "AS608";
const int DEVICE_PROTOCOL = 1;

LedState currentLedState = LED_BOOTING;
LedState currentRestoreState = LED_READY;
unsigned long ledStateStart = 0;
int currentPriority = 1;
int restorePriority = 2;

void setLedBrightness(uint8_t brightness) {
  ledcWrite(LED_PWM_CHANNEL, brightness);
}

int getPriorityForState(LedState state) {
  switch (state) {
    case LED_ERROR: return 8;
    case LED_COMMUNICATION_ERROR: return 7;
    case LED_SUCCESS: return 6;
    case LED_DB_ERROR: return 6;
    case LED_ENROLL: return 5;
    case LED_FIRMWARE: return 4;
    case LED_SCAN: return 3;
    case LED_HOST_CONNECTED: return 2;
    case LED_READY: return 2;
    case LED_BOOTING: return 1;
    case LED_HOST_DISCONNECTED: return 0;
    case LED_SLEEP: return 0;
    default: return 0;
  }
}

bool requestLedState(LedState state, bool temporary = false) {
  int priority = getPriorityForState(state);
  if (state == currentLedState) {
    return true;
  }

  if (currentPriority > priority && temporary) {
    return false;
  }

  if (temporary) {
    currentRestoreState = currentLedState;
    restorePriority = currentPriority;
  }

  currentLedState = state;
  currentPriority = priority;
  ledStateStart = millis();
  if (state == LED_BOOTING || state == LED_ERROR || state == LED_COMMUNICATION_ERROR || state == LED_DB_ERROR) {
    setLedBrightness(0);
  }
  return true;
}

void restoreLedStateIfNeeded() {
  int nowPriority = getPriorityForState(currentRestoreState);
  currentLedState = currentRestoreState;
  currentPriority = restorePriority;
  restorePriority = nowPriority;
  ledStateStart = millis();
}

void handleHostStatus(const String &status) {
  if (status == "HOST_CONNECTED") {
    requestLedState(LED_HOST_CONNECTED);
  } else if (status == "HOST_DISCONNECTED") {
    requestLedState(LED_HOST_DISCONNECTED);
  } else if (status == "DB_ERROR") {
    requestLedState(LED_DB_ERROR, true);
  } else if (status == "FIRMWARE") {
    requestLedState(LED_FIRMWARE);
  } else if (status == "READY") {
    requestLedState(LED_READY);
  }
}

String parseJsonStringField(const String &json, const String &field) {
  String key = "\"" + field + "\"";
  int keyIndex = json.indexOf(key);
  if (keyIndex < 0) {
    return "";
  }
  int colonIndex = json.indexOf(':', keyIndex + key.length());
  if (colonIndex < 0) {
    return "";
  }
  int startQuote = json.indexOf('"', colonIndex);
  if (startQuote < 0) {
    return "";
  }
  int endQuote = json.indexOf('"', startQuote + 1);
  if (endQuote < 0) {
    return "";
  }
  return json.substring(startQuote + 1, endQuote);
}

void emitJsonStatus(const String &state) {
  Serial.print("{\"type\":\"status\",\"state\":\"");
  Serial.print(state);
  Serial.println("\"}");
}

void emitJsonAttendanceMatch(int id, int confidence) {
  Serial.print("{\"type\":\"attendance\",\"event\":\"match\",\"id\":");
  Serial.print(id);
  Serial.print(",\"confidence\":");
  Serial.print(confidence);
  Serial.println("}");
}

void emitJsonAttendanceUnknown() {
  Serial.println("{\"type\":\"attendance\",\"event\":\"unknown\"}");
}

void emitJsonAttendanceLowConfidence(int confidence) {
  Serial.print("{\"type\":\"attendance\",\"event\":\"low_confidence\",\"confidence\":");
  Serial.print(confidence);
  Serial.println("}");
}

void beginLedManager() {
  pinMode(LED_PIN, OUTPUT);
  ledcSetup(LED_PWM_CHANNEL, LED_PWM_FREQUENCY, LED_PWM_RESOLUTION);
  ledcAttachPin(LED_PIN, LED_PWM_CHANNEL);
  currentPriority = getPriorityForState(LED_BOOTING);
  requestLedState(LED_BOOTING);
}

void ledReady() {
  requestLedState(LED_READY);
}

void ledScan() {
  requestLedState(LED_SCAN);
}

void ledEnroll() {
  requestLedState(LED_ENROLL);
}

void ledSuccess() {
  requestLedState(LED_SUCCESS, true);
}

void ledError() {
  requestLedState(LED_ERROR, true);
}

void ledSleep() {
  requestLedState(LED_SLEEP);
}

void ledFirmware() {
  requestLedState(LED_FIRMWARE);
}

void ledHostConnected() {
  requestLedState(LED_HOST_CONNECTED);
}

void ledHostDisconnected() {
  requestLedState(LED_HOST_DISCONNECTED);
}

uint8_t computeBootBrightness(unsigned long elapsed) {
  unsigned long phase = elapsed % BOOT_PULSE_PERIOD_MS;
  unsigned long half = BOOT_PULSE_PERIOD_MS / 2;
  if (phase < half) {
    return (uint8_t) map(phase, 0, half, 0, LED_MAX_BRIGHTNESS);
  }
  return (uint8_t) map(phase, half, BOOT_PULSE_PERIOD_MS, LED_MAX_BRIGHTNESS, 0);
}

void updateLed() {
  unsigned long now = millis();
  unsigned long elapsed = now - ledStateStart;

  switch (currentLedState) {
    case LED_BOOTING: {
      setLedBrightness(computeBootBrightness(elapsed));
      break;
    }
    case LED_READY:
    case LED_HOST_CONNECTED: {
      unsigned long phase = elapsed % READY_PERIOD_MS;
      setLedBrightness(phase < READY_ON_MS ? LED_MAX_BRIGHTNESS : 0);
      break;
    }
    case LED_SCAN: {
      unsigned long phase = elapsed % (SCAN_PULSE_MS * 2);
      setLedBrightness(phase < SCAN_PULSE_MS ? LED_MAX_BRIGHTNESS : 0);
      break;
    }
    case LED_SUCCESS: {
      if (elapsed >= SUCCESS_TOTAL_MS) {
        restoreLedStateIfNeeded();
        break;
      }
      setLedBrightness(LED_MAX_BRIGHTNESS);
      break;
    }
    case LED_ENROLL: {
      unsigned long cycleTime = ENROLL_COUNT * (ENROLL_ON_MS + ENROLL_OFF_MS) + ENROLL_END_OFF_MS;
      unsigned long phase = elapsed % cycleTime;
      if (phase < ENROLL_COUNT * (ENROLL_ON_MS + ENROLL_OFF_MS)) {
        unsigned long phaseInPulse = phase % (ENROLL_ON_MS + ENROLL_OFF_MS);
        setLedBrightness(phaseInPulse < ENROLL_ON_MS ? LED_MAX_BRIGHTNESS : 0);
      } else {
        setLedBrightness(0);
      }
      break;
    }
    case LED_FIRMWARE: {
      unsigned long phase = elapsed % (FIRMWARE_BLINK_MS * 2);
      setLedBrightness(phase < FIRMWARE_BLINK_MS ? LED_MAX_BRIGHTNESS : 0);
      break;
    }
    case LED_ERROR:
    case LED_DB_ERROR: {
      if (elapsed >= ERROR_TOTAL_MS) {
        restoreLedStateIfNeeded();
        break;
      }
      unsigned long phase = elapsed % (ERROR_BLINK_MS * 2);
      setLedBrightness(phase < ERROR_BLINK_MS ? LED_MAX_BRIGHTNESS : 0);
      break;
    }
    case LED_COMMUNICATION_ERROR: {
      unsigned long phase = elapsed % (COMM_ERROR_ON_MS + COMM_ERROR_OFF_MS);
      setLedBrightness(phase < COMM_ERROR_ON_MS ? LED_MAX_BRIGHTNESS : 0);
      break;
    }
    case LED_HOST_DISCONNECTED:
    case LED_SLEEP: {
      setLedBrightness(0);
      break;
    }
  }
}

// ── Mode ──────────────────────────────────────────────────────────────────────
bool scanMode = false;  // false = command mode, true = scan mode
String pendingCommand = "";

// NOTE: The firmware is intentionally kept in a single sketch for now.
// If it grows further, the LED logic, command handling, and fingerprint flow
// can later be split into separate .h/.cpp files for maintainability.


// ==============================================================================
//  SETUP
// ==============================================================================

void setup() {
  beginLedManager();

  Serial.begin(115200);
  unsigned long bootStart = millis();
  while (millis() - bootStart < 1000) {
    updateLed();
    delay(10);
  }

  Serial.println("\n========================================");
  Serial.println("  AS608 All-in-One Fingerprint System");
  Serial.println("========================================");
  Serial.print("{\"device\": \"");
  Serial.print(DEVICE_IDENTIFIER);
  Serial.print("\", \"board\": \"");
  Serial.print(DEVICE_BOARD);
  Serial.print("\", \"firmware\": \"");
  Serial.print(DEVICE_FIRMWARE);
  Serial.print("\", \"sensor\": \"");
  Serial.print(DEVICE_SENSOR);
  Serial.print("\", \"protocol\": ");
  Serial.print(DEVICE_PROTOCOL);
  Serial.print(", \"serial_number\": \"");
  Serial.print(ESP.getEfuseMac());
  Serial.println("\"}");

  mySerial.begin(57600, SERIAL_8N1, FINGERPRINT_RX, FINGERPRINT_TX);
  finger.begin(57600);

  if (finger.verifyPassword()) {
    Serial.println("Sensor found!");
    ledReady();
  } else {
    Serial.println("ERROR: Sensor not found. Check wiring.");
    ledError();
    while (1) {
      updateLed();
      delay(1);
    }
  }

  finger.getTemplateCount();
  Serial.print("Stored fingerprints: ");
  Serial.println(finger.templateCount);

  printHelp();
  Serial.println("READY");
  emitJsonStatus("READY");
}


// ==============================================================================
//  LOOP
// ==============================================================================

void loop() {
  updateLed();

  // Process any pending command that was received during enrollment.
  if (pendingCommand.length() > 0) {
    String cmd = pendingCommand;
    pendingCommand = "";
    handleCommand(cmd);
    return;
  }

  // Check for Serial commands from PC
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    handleCommand(input);
  }

  // If in scan mode, keep scanning for fingers
  if (scanMode) {
    scanFinger();
  }
}


// ==============================================================================
//  COMMAND HANDLER
// ==============================================================================

void handleCommand(String input) {
  input.toUpperCase();

  // ── IDENTIFY ───────────────────────────────────────────────────
  if (input == "ID?") {
    Serial.print("{\"device\": \"");
    Serial.print(DEVICE_IDENTIFIER);
    Serial.print("\", \"board\": \"");
    Serial.print(DEVICE_BOARD);
    Serial.print("\", \"firmware\": \"");
    Serial.print(DEVICE_FIRMWARE);
    Serial.print("\", \"sensor\": \"");
    Serial.print(DEVICE_SENSOR);
    Serial.print("\", \"protocol\": ");
    Serial.print(DEVICE_PROTOCOL);
    Serial.print(", \"serial_number\": \"");
    Serial.print(ESP.getEfuseMac());
    Serial.println("\"}");
    return;
  }

  // ── SCAN ──────────────────────────────────────────────────────
  if (input == "SCAN") {
    scanMode = true;
    ledScan();
    Serial.println("\n>> Switched to SCAN MODE");
    Serial.println("   Place finger on sensor to log attendance.");
    Serial.println("   Type STOP to return to command mode.");
    Serial.println("SCAN_MODE");
    emitJsonStatus("SCAN_MODE");
    return;
  }

  // ── STOP ──────────────────────────────────────────────────────
  if (input == "STOP") {
    scanMode = false;
    ledReady();
    Serial.println("\n>> Switched to COMMAND MODE");
    printHelp();
    Serial.println("CMD_MODE");
    emitJsonStatus("CMD_MODE");
    return;
  }

  // ── LIST ──────────────────────────────────────────────────────
  if (input == "LIST") {
    scanMode = false;
    ledReady();
    finger.getTemplateCount();
    Serial.print("\n>> Stored fingerprints: ");
    Serial.println(finger.templateCount);
    Serial.println("CMD_MODE");
    return;
  }

  // ── WIPE ──────────────────────────────────────────────────────
  if (input == "WIPE") {
    scanMode = false;
    ledReady();
    Serial.println("\n>> Wiping ALL fingerprints...");
    if (finger.emptyDatabase() == FINGERPRINT_OK) {
      Serial.println("   SUCCESS - All fingerprints deleted.");
    } else {
      Serial.println("   FAILED - Could not wipe database.");
    }
    Serial.println("CMD_MODE");
    return;
  }

  // ── ENROLL / ENROLL:ID ──────────────────────────────────────
  if (input == "ENROLL") {
    int id = findNextAvailableId();
    if (id <= 0) {
      Serial.println("ERROR: No free fingerprint slots available. Delete one first.");
      ledReady();
      return;
    }
    ledEnroll();
    scanMode = false; // pause scanning during enrollment
    enrollFinger(id);
    return;
  }

  if (input.startsWith("ENROLL:")) {
    int id = input.substring(7).toInt();
    if (id < 1 || id > 127) {
      Serial.println("ERROR: ID must be between 1 and 127. Example: ENROLL:5");
      ledReady();
      return;
    }
    ledEnroll();
    scanMode = false; // pause scanning during enrollment
    enrollFinger(id);
    return;
  }

  // ── DELETE:ID ─────────────────────────────────────────────────
  if (input.startsWith("DELETE:")) {
    ledReady();
    int id = input.substring(7).toInt();
    if (id < 1 || id > 127) {
      Serial.println("ERROR: ID must be between 1 and 127. Example: DELETE:5");
      return;
    }
    Serial.print("\n>> Deleting ID #");
    Serial.print(id);
    Serial.println("...");
    if (finger.deleteModel(id) == FINGERPRINT_OK) {
      Serial.print("   SUCCESS - ID #");
      Serial.print(id);
      Serial.println(" deleted.");
    } else {
      Serial.print("   FAILED - Could not delete ID #");
      Serial.print(id);
      Serial.println(" (may not exist)");
    }
    return;
  }

  if (input.startsWith("STATUS:")) {
    String state = input.substring(7);
    state.trim();
    handleHostStatus(state);
    return;
  }

  if (input.startsWith("{")) {
    String type = parseJsonStringField(input, "type");
    if (type == "status") {
      String state = parseJsonStringField(input, "state");
      if (state.length() > 0) {
        handleHostStatus(state);
      }
      return;
    }
  }

  // ── UNKNOWN COMMAND ───────────────────────────────────────────
  Serial.println("Unknown command. Type HELP to see commands.");
  printHelp();
}


// ==============================================================================
//  ENROLL HELPERS
// ==============================================================================

bool fingerprintExists(uint8_t id) {
  uint8_t p = finger.loadModel(id);
  return p == FINGERPRINT_OK;
}

int findNextAvailableId() {
  for (int id = 1; id <= 127; ++id) {
    if (!fingerprintExists(id)) {
      return id;
    }
  }
  return -1;
}

bool checkEnrollmentCancel() {
  if (!Serial.available()) {
    updateLed();
    return false;
  }

  String input = Serial.readStringUntil('\n');
  input.trim();
  input.toUpperCase();

  if (input == "STOP") {
    ledReady();
    Serial.println("\n>> Enrollment cancelled.");
    Serial.println("ENROLLMENT cancelled.");
    Serial.println("CMD_MODE");
    return true;
  }

  if (input.startsWith("DELETE:") || input.startsWith("ENROLL") || input == "WIPE" || input == "LIST" || input == "SCAN") {
    pendingCommand = input;
    ledReady();
    Serial.println("\n>> Enrollment cancelled due to a new command.");
    Serial.println("ENROLLMENT cancelled.");
    Serial.println("CMD_MODE");
    return true;
  }

  if (input.length() > 0) {
    Serial.println("Enrollment is in progress. Type STOP to cancel.");
  }
  return false;
}

// ==============================================================================
//  ENROLL
// ==============================================================================

void enrollFinger(int id) {
  ledEnroll();
  Serial.println();
  Serial.println("----------------------------------------");
  Serial.print("  ENROLLING FINGER AS ID #");
  Serial.println(id);
  Serial.println("----------------------------------------");

  int p = -1;

  // ── SCAN 1 ────────────────────────────────────────────────────
  Serial.println("Step 1: Place finger on sensor...");
  while (p != FINGERPRINT_OK) {
    if (checkEnrollmentCancel()) {
      return;
    }
    p = finger.getImage();
    if (p == FINGERPRINT_NOFINGER) { delay(50); continue; }
    if (p == FINGERPRINT_OK)       { Serial.println("\n  Image taken!"); break; }
    Serial.println("  Imaging error, try again.");
  }

  p = finger.image2Tz(1);
  if (p != FINGERPRINT_OK) {
    Serial.println("  ERROR: Could not convert image. Try again.");
    Serial.println("  Tip: Press finger flat and firm on the sensor.");
    return;
  }
  Serial.println("  Image converted.");

  // ── LIFT FINGER ───────────────────────────────────────────────
  Serial.println("Step 2: Remove finger...");
  unsigned long start_wait = millis();
  while (millis() - start_wait < 2000) {
    updateLed();
    if (checkEnrollmentCancel()) {
      return;
    }
    delay(50);
  }
  p = 0;
  while (p != FINGERPRINT_NOFINGER) {
    updateLed();
    if (checkEnrollmentCancel()) {
      return;
    }
    p = finger.getImage();
  }
  Serial.println("  Finger removed.");

  // ── SCAN 2 ────────────────────────────────────────────────────
  Serial.println("Step 3: Place the SAME finger again...");
  p = -1;
  while (p != FINGERPRINT_OK) {
    if (checkEnrollmentCancel()) {
      return;
    }
    p = finger.getImage();
    if (p == FINGERPRINT_NOFINGER) { delay(50); continue; }
    if (p == FINGERPRINT_OK)       { Serial.println("\n  Image taken!"); break; }
    Serial.println("  Imaging error, try again.");
  }

  p = finger.image2Tz(2);
  if (p != FINGERPRINT_OK) {
    Serial.println("  ERROR: Could not convert image. Try again.");
    return;
  }
  Serial.println("  Image converted.");

  // ── CREATE MODEL ──────────────────────────────────────────────
  p = finger.createModel();
  if (p == FINGERPRINT_ENROLLMISMATCH) {
    ledError();
    Serial.println("  ERROR: Fingerprints did not match.");
    Serial.println("  Tip: Use the SAME finger, same position, both times.");
    Serial.print("  Type ENROLL:");
    Serial.print(id);
    Serial.println(" to try again.");
    return;
  }
  if (p != FINGERPRINT_OK) {
    ledError();
    Serial.println("  ERROR: Could not create model.");
    return;
  }

  // ── STORE ─────────────────────────────────────────────────────
  p = finger.storeModel(id);
  if (p == FINGERPRINT_OK) {
    ledSuccess();
    Serial.println("----------------------------------------");
    Serial.print("  SUCCESS! Finger saved as ID #");
    Serial.println(id);
    Serial.println("----------------------------------------");
    finger.getTemplateCount();
    Serial.print("  Total stored: ");
    Serial.println(finger.templateCount);
    Serial.println();
  } else {
    ledError();
    Serial.println("  ERROR: Could not store fingerprint.");
  }
}


// ==============================================================================
//  SCAN (Attendance Mode)
// ==============================================================================

void scanFinger() {
  uint8_t p = finger.getImage();
  if (p == FINGERPRINT_NOFINGER) return;
  if (p != FINGERPRINT_OK)       return;

  p = finger.image2Tz();
  if (p != FINGERPRINT_OK) return;

  p = finger.fingerSearch();
  if (p == FINGERPRINT_OK) {
    if (finger.confidence >= MIN_CONFIDENCE) {
      ledSuccess();
      emitJsonAttendanceMatch(finger.fingerID, finger.confidence);
    } else {
      emitJsonAttendanceLowConfidence(finger.confidence);
    }
    delay(SCAN_COOLDOWN);
  } else if (p == FINGERPRINT_NOTFOUND) {
    emitJsonAttendanceUnknown();
    delay(1000);
  }
}


// ==============================================================================
//  HELP
// ==============================================================================

void printHelp() {
  Serial.println();
  Serial.println("  Commands (line ending must be set to Newline):");
  Serial.println("    ENROLL     Enroll finger using next free ID");
  Serial.println("    ENROLL:1   Enroll finger as ID 1  (1-127)");
  Serial.println("    DELETE:1   Delete finger ID 1");
  Serial.println("    WIPE       Delete ALL fingerprints");
  Serial.println("    LIST       Show stored fingerprint count");
  Serial.println("    SCAN       Start attendance scan mode");
  Serial.println("    STOP       Stop scanning, return to commands");
  Serial.println();
}
