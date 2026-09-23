/*
  RC522 + ESP32 - UID Read Test
  ------------------------------
  Wiring (matches your setup):
    RC522 SDA  -> GPIO 5   (SS)
    RC522 SCK  -> GPIO 18
    RC522 MOSI -> GPIO 23
    RC522 MISO -> GPIO 19
    RC522 IRQ  -> not connected
    RC522 GND  -> GND
    RC522 RST  -> GPIO 4
    RC522 3.3V -> 3V3   (NEVER 5V, will fry the module)

  Library needed: "MFRC522" by GithubCommunity
  (Arduino IDE -> Sketch -> Include Library -> Manage Libraries -> search "MFRC522")
*/

#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN   5
#define RST_PIN  4

MFRC522 rfid(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(115200);
  while (!Serial);

  SPI.begin();          // uses default ESP32 VSPI pins: SCK 18, MISO 19, MOSI 23
  rfid.PCD_Init();

  Serial.println();
  Serial.println("RC522 initialized. Scan a card/tag...");

  // Optional: print firmware version to confirm SPI wiring is good.
  // 0x00 or 0xFF usually means wiring/power issue.
  byte version = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  Serial.print("MFRC522 firmware version: 0x");
  Serial.println(version, HEX);
}

void loop() {
  // Look for a new card
  if (!rfid.PICC_IsNewCardPresent()) return;

  // Try to read its UID
  if (!rfid.PICC_ReadCardSerial()) return;

  Serial.print("UID tag: ");
  String uidStr = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uidStr += "0";
    uidStr += String(rfid.uid.uidByte[i], HEX);
    if (i != rfid.uid.size - 1) uidStr += ":";
  }
  uidStr.toUpperCase();
  Serial.println(uidStr);

  // Print PICC type (card type)
  MFRC522::PICC_Type piccType = rfid.PICC_GetType(rfid.uid.sak);
  Serial.print("PICC type: ");
  Serial.println(rfid.PICC_GetTypeName(piccType));

  Serial.println("------------------------");

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}
