/*
  RC522 + ESP32 - Read text from card
  --------------------------------------
  Reads the 16-byte string previously written into Sector 1 / Block 4.

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

void setup() {
  Serial.begin(115200);
  while (!Serial);

  SPI.begin();
  rfid.PCD_Init();

  for (byte i = 0; i < 6; i++) key.keyByte[i] = 0xFF;

  Serial.println("Place card near reader to READ...");
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

  MFRC522::StatusCode status = rfid.PCD_Authenticate(
      MFRC522::PICC_CMD_MF_AUTH_KEY_A, BLOCK_NUM, &key, &(rfid.uid));

  if (status != MFRC522::STATUS_OK) {
    Serial.print("Auth failed: ");
    Serial.println(rfid.GetStatusCodeName(status));
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
    return;
  }

  byte buffer[18]; // MIFARE_Read needs 2 extra bytes for CRC
  byte size = 18;

  status = rfid.MIFARE_Read(BLOCK_NUM, buffer, &size);

  if (status == MFRC522::STATUS_OK) {
    String result = "";
    for (byte i = 0; i < 16; i++) result += (char)buffer[i];
    result.trim(); // remove padding spaces
    Serial.print("Data on card: \"");
    Serial.print(result);
    Serial.println("\"");
  } else {
    Serial.print("Read FAILED: ");
    Serial.println(rfid.GetStatusCodeName(status));
  }

  Serial.println("------------------------");

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  delay(1500);
}
