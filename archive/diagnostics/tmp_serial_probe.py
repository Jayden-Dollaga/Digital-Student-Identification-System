import serial
import time

port = 'COM4'
baud = 115200
print('Opening', port, baud)
ser = serial.Serial(port, baud, timeout=0.05)
print('Opened; dtr=', ser.dtr, 'rts=', ser.rts, 'in_waiting=', ser.in_waiting)
for i in range(30):
    n = ser.in_waiting
    if n:
        data = ser.read(n)
        print(f'CHUNK {i}:', repr(data), 'len', len(data))
        if b'FLASH_BOOT' in data:
            print('contains FLASH_BOOT')
            break
    else:
        time.sleep(0.01)
ser.close()
print('Closed')
