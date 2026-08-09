import serial
import time

port = 'COM4'
baud = 115200

print('Opening port with manual DTR control')
ser = serial.Serial()
ser.port = port
ser.baudrate = baud
ser.timeout = 0.05
ser.dtr = False
ser.rts = False
ser.open()
print('opened', ser, 'dtr', ser.dtr, 'rts', ser.rts)
ser.setDTR(False)
ser.setRTS(False)
# Give the port a moment to settle.
time.sleep(0.1)
print('reading buffer after open, before toggle', ser.in_waiting)
if ser.in_waiting:
    data = ser.read(ser.in_waiting)
    print('initial data', repr(data))

print('pulsing DTR for reset')
ser.setDTR(True)
# example pulse timing
time.sleep(0.1)
ser.setDTR(False)
time.sleep(0.1)

print('starting read loop')
buf = b''
for i in range(200):
    n = ser.in_waiting
    if n:
        data = ser.read(n)
        print('CHUNK', i, repr(data))
        buf += data
        if b'FLASH_BOOT' in buf:
            break
    time.sleep(0.01)

print('full buf prefix', repr(buf[:100]))
ser.close()
print('closed')
