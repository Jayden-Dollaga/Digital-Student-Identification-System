"""Historical serial compatibility module outside the active workflow."""

# Lightweight shim for environments without pyserial installed.
# Prefer real pyserial when available.
try:
    from serial import Serial as _RealSerial, SerialException as _RealSerialException
    # re-export directly
    Serial = _RealSerial
    SerialException = _RealSerialException
except Exception:
    class SerialException(Exception):
        pass

    class Serial:
        def __init__(self, *args, **kwargs):
            raise SerialException("pyserial is not installed in this environment. Install with 'pip install pyserial' to use real serial ports.")
        def close(self):
            pass
        def readline(self):
            return b""
        @property
        def in_waiting(self):
            return 0
