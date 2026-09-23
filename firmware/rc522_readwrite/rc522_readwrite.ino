/*
  RC522 + ESP32 - Combined Read/Write via Serial
  ------------------------------------------------
  Default mode: READ. Tap a card and it prints what's stored in Block 4.

  To WRITE instead:
    Type text into Serial Monitor and hit Enter.
    That arms "write mode" - the NEXT card you tap gets that text written
    to Block 4, then it auto-switches back to read mode.

  Special commands (type into Serial Monitor):
    r        -> force back to read mode (cancels pending write)

  Wiring: same as before
    SDA->5  SCK->18  MOSI->23  MISO->19  RST->4  GND->GND  3.3V->3V3
*/

#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN   5
#define RST_PIN  4

MFRC522 rfid(SS_PIN, RST_PIN);
MFRC522::MIFARE_Key key;

const byte BLOCK_NUM = 4;

bool writeMode = false;
String pendingWrite = "";

void setup() {
  Serial.begin(115200);
  while (!Serial);

  SPI.begin();
  rfid.PCD_Init();

  for (byte i = 0; i < 6; i++) key.keyByte[i] = 0xFF;

  Serial.println();
  Serial.println("=== RC522 Read/Write Tool ===");
  Serial.println("Type text + Enter to arm a WRITE.");
  Serial.println("Type 'r' + Enter to cancel and go back to READ mode.");
  Serial.println("Just tap a card with nothing typed to READ it.");
  Serial.println("------------------------------");
}

void loop() {
  checkSerialInput();

  if (!rfid.PICC_IsNewCardPresent()) return;
  if (!rfid.PICC_ReadCardSerial()) return;

  Serial.print("Card UID: ");
  for (byte i = 0; i < rfid.uid.size; i++) {
    Serial.print(rfid.uid.uidByte[i] < 0x10 ? " 0" : " ");
    Serial.print(rfid.uid.uidByte[i], HEX);
  }
  Serial.println();

  MFRC522::StatusCode status = rfid.PCD_Authenticate(
      MFRC522::PICC_CMD_MF_AUTH_KEY_A, BLOCK_NUM, &key, &(rfid.uid));

  if (status != MFRC522::STATUS_OK) {
    Serial.print("Auth failed: ");
    Serial.println(rfid.GetStatusCodeName(status));
    haltAndReturn();
    return;
  }

  if (writeMode) {
    doWrite();
    writeMode = false; // auto revert to read mode after one write
    pendingWrite = "";
  } else {
    doRead();
  }

  Serial.println("------------------------");
  haltAndReturn();
}

void checkSerialInput() {
  if (!Serial.available()) return;

  String input = Serial.readStringUntil('\n');
  input.trim();
  if (input.length() == 0) return;

  if (input.equalsIgnoreCase("r")) {
    writeMode = false;
    pendingWrite = "";
    Serial.println(">> Read mode. Tap a card.");
    return;
  }

  pendingWrite = input;
  writeMode = true;
  Serial.print(">> Write armed: \"");
  Serial.print(pendingWrite);
  Serial.println("\" - tap a card now to write it.");
}

void doWrite() {
  byte buffer[16];
  memset(buffer, ' ', 16);
  int len = pendingWrite.length();
  if (len > 16) len = 16;
  for (int i = 0; i < len; i++) buffer[i] = pendingWrite[i];

  MFRC522::StatusCode status = rfid.MIFARE_Write(BLOCK_NUM, buffer, 16);

  if (status == MFRC522::STATUS_OK) {
    Serial.print("Write SUCCESS: \"");
    Serial.print(pendingWrite);
    Serial.println("\"");
  } else {
    Serial.print("Write FAILED: ");
    Serial.println(rfid.GetStatusCodeName(status));
  }
}

void doRead() {
  byte buffer[18];
  byte size = 18;

  MFRC522::StatusCode status = rfid.MIFARE_Read(BLOCK_NUM, buffer, &size);

  if (status == MFRC522::STATUS_OK) {
    String result = "";
    for (byte i = 0; i < 16; i++) result += (char)buffer[i];
    result.trim();
    Serial.print("Data on card: \"");
    Serial.print(result);
    Serial.println("\"");
  } else {
    Serial.print("Read FAILED: ");
    Serial.println(rfid.GetStatusCodeName(status));
  }
}

void haltAndReturn() {
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(1000);
}
