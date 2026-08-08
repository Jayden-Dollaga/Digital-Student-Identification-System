import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python"))
import serial
from core.serial_handler import SerialHandler

print('Using pyserial', serial.VERSION)

# Direct raw serial read for boot capture validation.
for label, pre in [
    ("default flags", False),
    ("clear dtr/rts after open", True),
]:
    print('--- opening', label)
    ser = serial.Serial('COM4', 115200, timeout=0.2, dsrdtr=False, rtscts=False, xonxoff=False)
    if pre:
        ser.dtr = False
        ser.rts = False
    time.sleep(0.5)
    for i in range(20):
        raw = ser.read(ser.in_waiting or 1)
        if raw:
            print(f'RAW_CHUNK {i}:', repr(raw))
            try:
                print('DECODED', repr(raw.decode('utf-8', errors='replace')))
            except Exception as e:
                print('DECODE ERROR', e)
        else:
            print(f'RAW_CHUNK {i}: b""')
        time.sleep(0.05)
    ser.close()

print('--- now using SerialHandler ---')
handler = SerialHandler()
ok, msg = handler._attempt_connect('COM4', 115200)
print('connect', ok, msg)
if not ok:
    raise SystemExit('connect failed')

for i in range(50):
    line = handler.read_line()
    print(f'READ_LINE {i}:', repr(line))
    if line is not None and 'FLASH_BOOT' in line:
        break
    time.sleep(0.05)

handler.disconnect()
print('disconnected')
