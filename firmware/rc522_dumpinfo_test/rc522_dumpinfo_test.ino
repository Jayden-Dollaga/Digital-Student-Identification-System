/* DumpInfo test, adapted for the DSIS project's ESP32 + RC522 wiring.
 * Pins match RFID_SS_PIN / RFID_RST_PIN in ESP32_DSIS_AllInOne.ino:
 *   RST  -> GPIO 4
 *   SDA/SS -> GPIO 5
 *   SCK  -> GPIO 18 (ESP32 default VSPI)
 *   MOSI -> GPIO 23 (ESP32 default VSPI)
 *   MISO -> GPIO 19 (ESP32 default VSPI)
 *   3.3V -> RC522 VCC (NOT 5V/Vin - RC522 is 3.3V only)
 *   GND  -> GND
 *
 * Just uploads and dumps whatever it reads from any tapped card: UID, SAK,
 * PICC type, and a full sector-by-sector memory dump (using default key
 * FFFFFFFFFFFF for any sector it can authenticate).
 */

#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN   4   // matches RFID_RST_PIN in ESP32_DSIS_AllInOne.ino
#define SS_PIN    5   // matches RFID_SS_PIN in ESP32_DSIS_AllInOne.ino

MFRC522 mfrc522(SS_PIN, RST_PIN);  // Create MFRC522 instance

void setup() {
	Serial.begin(115200);   // match your other DSIS firmware's baud rate
	delay(500);              // ESP32 doesn't need while(!Serial), just a short settle delay
	SPI.begin();             // Init SPI bus (uses ESP32 default VSPI pins 18/19/23)
	mfrc522.PCD_Init();      // Init MFRC522
	mfrc522.PCD_DumpVersionToSerial();	// Show details of PCD - MFRC522 Card Reader details
	Serial.println(F("Scan PICC to see UID, SAK, type, and data blocks..."));
}

void loop() {
	// Look for new cards
	if ( ! mfrc522.PICC_IsNewCardPresent()) {
		return;
	}

	// Select one of the cards
	if ( ! mfrc522.PICC_ReadCardSerial()) {
		return;
	}

	// Dump debug info about the card; PICC_HaltA() is automatically called
	mfrc522.PICC_DumpToSerial(&(mfrc522.uid));
}
