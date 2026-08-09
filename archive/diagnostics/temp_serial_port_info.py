from serial.tools import list_ports

for port in list_ports.comports():
    print('device=' + str(port.device))
    print('description=' + str(port.description))
    print('hwid=' + str(port.hwid))
    print('vid=' + str(getattr(port, 'vid', None)))
    print('pid=' + str(getattr(port, 'pid', None)))
    print('manufacturer=' + str(getattr(port, 'manufacturer', None)))
    print('product=' + str(getattr(port, 'product', None)))
    print('serial_number=' + str(getattr(port, 'serial_number', None)))
    print('location=' + str(getattr(port, 'location', None)))
    print('---')
