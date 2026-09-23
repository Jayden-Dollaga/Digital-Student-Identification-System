/*
  RC522 + ESP32 - Write text to card
  ------------------------------------
  Writes a 16-byte string into Sector 1 / Block 4 of a MIFARE Classic card.
  Uses default factory key (FF FF FF FF FF FF) for authentication.

  Wiring: same as before
    SDA->5  SCK->18  MOSI->23  MISO->19  RST->4  GND->GND  3.3V->3V3
*/

#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN   5
#define RST_PIN  4

MFRC522 rfid(SS_PIN, RST_PIN);
MFRC522::MIFARE_Key key;

const byte BLOCK_NUM = 4; // block 4 = first data block of sector 1

// <<< CHANGE THIS to whatever you want to store, e.g. a student ID >>>
String dataToWrite = "JAYDEN-0001";

void setup() {
  Serial.begin(115200);
  while (!Serial);

  SPI.begin();
  rfid.PCD_Init();

  // default key = all 0xFF
  for (byte i = 0; i < 6; i++) key.keyByte[i] = 0xFF;

  Serial.println("Place card near reader to WRITE...");
}

void loop() {
  if (!rfid.PICC_IsNewCardPresent()) return;
  if (!rfid.PICC_ReadCardSerial()) return;

  Serial.print("Card UID: ");
  for (byte i = 0; i < rfid.uid.size; i++) {
    Serial.print(rfid.uid.uidByte[i] < 0x10 ? " 0" : " ");
    Serial.print(rfid.uid.uidByte[i], HEX);
  }
  Serial.println();

  // Authenticate block using key A
  MFRC522::StatusCode status = rfid.PCD_Authenticate(
      MFRC522::PICC_CMD_MF_AUTH_KEY_A, BLOCK_NUM, &key, &(rfid.uid));

  if (status != MFRC522::STATUS_OK) {
    Serial.print("Auth failed: ");
    Serial.println(rfid.GetStatusCodeName(status));
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
    return;
  }

  // Prepare exactly 16 bytes (pad with spaces, truncate if too long)
  byte buffer[16];
  memset(buffer, ' ', 16);
  int len = dataToWrite.length();
  if (len > 16) len = 16;
  for (int i = 0; i < len; i++) buffer[i] = dataToWrite[i];

  status = rfid.MIFARE_Write(BLOCK_NUM, buffer, 16);

  if (status == MFRC522::STATUS_OK) {
    Serial.print("Write SUCCESS: \"");
    Serial.print(dataToWrite);
    Serial.println("\"");
  } else {
    Serial.print("Write FAILED: ");
    Serial.println(rfid.GetStatusCodeName(status));
  }

  Serial.println("------------------------");

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  delay(1500); // small cooldown before next scan
}
