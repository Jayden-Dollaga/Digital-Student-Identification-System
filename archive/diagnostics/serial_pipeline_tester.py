import argparse
import sys
import time

try:
    import serial
    from serial.tools import list_ports
except Exception as exc:
    serial = None
    list_ports = None
    print(f"ERROR: pyserial is required for live testing: {exc}")


def list_ports_available():
    if list_ports is None:
        return []
    return [port.device for port in list_ports.comports()]


def print_bytes(label, data):
    print(f"[{label}] {len(data)} bytes: {data!r}")


def open_serial(port, baud, timeout=1.0):
    if serial is None:
        raise RuntimeError("pyserial not installed")
    return serial.Serial(port, baud, timeout=timeout)


def capture_port(port, baud, duration, show_raw=True):
    with open_serial(port, baud, timeout=0.1) as ser:
        print(f"Connected to {port} at {baud} baud")
        print(f"Using timeout={ser.timeout}")
        start = time.time()
        buffer = b""
        line_count = 0
        while time.time() - start < duration:
            raw = ser.read(ser.in_waiting or 1)
            if raw:
                if show_raw:
                    print_bytes("RAW", raw)
                buffer += raw
                while b"\n" in buffer:
                    line, sep, buffer = buffer.partition(b"\n")
                    line_count += 1
                    line_text = line.decode("utf-8", errors="replace")
                    print(f"[LINE {line_count}] repr={line_text!r}")
            else:
                time.sleep(0.01)
        if buffer:
            print(f"[REMAINDER] {buffer!r}")
        print(f"Captured {line_count} complete lines")


def replay_file(path):
    with open(path, "rb") as fh:
        data = fh.read()
    print_bytes("FILE", data)
    buffer = b""
    line_count = 0
    buffer += data
    while b"\n" in buffer:
        line, sep, buffer = buffer.partition(b"\n")
        line_count += 1
        line_text = line.decode("utf-8", errors="replace")
        print(f"[LINE {line_count}] repr={line_text!r}")
    if buffer:
        print(f"[REMAINDER] {buffer!r}")
    print(f"Replayed {line_count} complete lines")


def main():
    parser = argparse.ArgumentParser(description="ESP32 serial pipeline diagnostic tester")
    parser.add_argument("--port", help="Serial port to open")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("--duration", type=float, default=5.0, help="Seconds to capture")
    parser.add_argument("--input", help="Replay raw serial capture from file")
    parser.add_argument("--list", action="store_true", help="List available serial ports")
    parser.add_argument("--no-raw", action="store_true", help="Do not print raw byte chunks")
    args = parser.parse_args()

    if args.list:
        ports = list_ports_available()
        print("Available ports:")
        for p in ports:
            print(f"  {p}")
        return

    if args.input:
        replay_file(args.input)
        return

    if not args.port:
        parser.error("--port is required for live capture")

    capture_port(args.port, args.baud, args.duration, show_raw=not args.no_raw)


if __name__ == "__main__":
    main()
