import os
import sys
import time

sys.path.insert(0, os.path.join(os.getcwd(), "python"))
from core.serial_handler import SerialHandler

handler = SerialHandler()
print('Connecting via SerialHandler.connect() with discovery/handshake...')
ok, msg = handler.connect('COM4', 115200, auto_detect=False)
print('connect', ok, msg)
if not ok:
    raise SystemExit('connect failed')

for i in range(60):
    line = handler.read_line()
    if line is not None:
        print(f'LINE {i}: {repr(line)}')
        if 'FLASH_BOOT' in line:
            break
    time.sleep(0.05)

handler.disconnect()
print('done')
