#!/usr/bin/env python3
import argparse
import threading
import sys
import time
from datetime import datetime

try:
    import serial
    from serial import SerialException
except ImportError:
    sys.stderr.write("ERROR: pyserial is required. Install with `pip install pyserial`.\n")
    sys.exit(1)


class SerialMonitor:
    def __init__(self, port, baudrate, timeout, raw_mode, hex_mode):
        self.port_name = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.raw_mode = raw_mode
        self.hex_mode = hex_mode
        self.serial_port = None
        self.stop_event = threading.Event()
        self.reader_thread = None
        self.input_thread = None
        self.open_time = None
        self.first_byte_time = None
        self.bytes_received = 0
        self.lines_received = 0
        self.last_data = b""
        self.exception = None
        self.first_byte_received = threading.Event()

    def open(self):
        self.serial_port = serial.Serial(
            port=self.port_name,
            baudrate=self.baudrate,
            timeout=self.timeout,
            dsrdtr=False,
            rtscts=False,
            xonxoff=False,
        )
        self.serial_port.dtr = False
        self.serial_port.rts = False
        try:
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
        except (SerialException, OSError):
            pass
        self.open_time = datetime.now()
        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()

    def close(self):
        self.stop_event.set()
        if self.reader_thread is not None:
            self.reader_thread.join(timeout=2)
        if self.input_thread is not None:
            self.input_thread.join(timeout=2)
        if self.serial_port is not None and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception:
                pass

    def _reader_loop(self):
        while not self.stop_event.is_set():
            try:
                data = self.serial_port.read(1024)
            except (SerialException, OSError) as exc:
                self.exception = exc
                self._report_disconnection(exc)
                self.stop_event.set()
                break

            if not data:
                continue

            now = datetime.now()
            if self.first_byte_time is None:
                self.first_byte_time = now
                self.first_byte_received.set()

            self.bytes_received += len(data)
            self.lines_received += data.count(b"\n")
            self.last_data = data

            if self.hex_mode:
                hex_line = "RX HEX: " + " ".join(f"{byte:02X}" for byte in data)
                sys.stdout.write(hex_line + "\n")
                sys.stdout.flush()

            if self.raw_mode:
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
            else:
                try:
                    sys.stdout.write(data.decode("utf-8", errors="replace"))
                except Exception:
                    sys.stdout.buffer.write(data)
                sys.stdout.flush()

    def _report_disconnection(self, exc):
        sys.stderr.write("SERIAL DISCONNECTED\n")
        sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
        sys.stderr.flush()

    def start_input_loop(self):
        self.input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self.input_thread.start()

    def _input_loop(self):
        while not self.stop_event.is_set():
            try:
                command = input("> ")
            except EOFError:
                self.stop_event.set()
                break
            except KeyboardInterrupt:
                self.stop_event.set()
                break

            if command.strip().lower() in {"exit", "quit"}:
                self.stop_event.set()
                break

            line = command + "\n"
            try:
                self.serial_port.write(line.encode("utf-8"))
                self.serial_port.flush()
            except (SerialException, OSError) as exc:
                self.exception = exc
                self._report_disconnection(exc)
                self.stop_event.set()
                break

    def send_command(self, command):
        if self.serial_port is None or not self.serial_port.is_open:
            return False
        try:
            payload = f"{command}\n".encode("utf-8")
            self.serial_port.write(payload)
            self.serial_port.flush()
            return True
        except (SerialException, OSError) as exc:
            self.exception = exc
            self._report_disconnection(exc)
            self.stop_event.set()
            return False

    def wait_for_first_byte(self, timeout):
        return self.first_byte_received.wait(timeout=timeout)

    def get_summary(self):
        summary = {
            "port": self.port_name,
            "baud": self.baudrate,
            "dtr": False,
            "rts": False,
            "bytes_received": self.bytes_received,
            "lines_received": self.lines_received,
            "time_opened": self.open_time,
            "first_byte_time": self.first_byte_time,
            "last_data": self.last_data,
            "exception": self.exception,
        }
        return summary


def parse_args():
    parser = argparse.ArgumentParser(
        description="Standalone raw serial monitor for ESP32 fingerprint attendance system."
    )
    parser.add_argument(
        "--port",
        default="COM4",
        help="Serial port to open (default: COM4)",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=115200,
        help="Baud rate (default: 115200)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=0.05,
        help="Serial read timeout in seconds (default: 0.05)",
    )
    parser.add_argument(
        "--hex",
        action="store_true",
        help="Show received bytes in HEX alongside raw text output.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Write raw decoded serial data to stdout with minimum processing.",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run automated command test mode using LIST, SCAN, STOP.",
    )
    return parser.parse_args()


def print_status(summary):
    print("\n--- SERIAL MONITOR DIAGNOSTIC SUMMARY ---")
    print(f"Port: {summary['port']}")
    print(f"Baud: {summary['baud']}")
    print(f"DTR: {summary['dtr']}")
    print(f"RTS: {summary['rts']}")
    if summary["time_opened"]:
        print(f"Port opened: {summary['time_opened'].isoformat()}")
    if summary["first_byte_time"]:
        elapsed = summary["first_byte_time"] - summary["time_opened"]
        print(f"First byte received after: {elapsed.total_seconds():.3f}s")
    print(f"Bytes received: {summary['bytes_received']}")
    print(f"Lines received: {summary['lines_received']}")
    print(f"Last received raw bytes: {summary['last_data']!r}")
    if summary["exception"]:
        print(f"Serial exception: {type(summary['exception']).__name__}: {summary['exception']}")
    else:
        print("Serial exception: None")
    print("--- END DIAGNOSTIC SUMMARY ---")


def automated_test(monitor):
    test_delay = 2.5
    boot_wait = 12.0
    print(f"Waiting up to {boot_wait:.1f}s for incoming serial data...")
    monitor.wait_for_first_byte(timeout=boot_wait)
    print("Boot capture phase complete. Sending commands in sequence.")
    for command in ["LIST", "SCAN", "STOP"]:
        if monitor.stop_event.is_set():
            break
        print(f"\n--- SENDING COMMAND: {command} ---")
        success = monitor.send_command(command)
        print(f"Command sent: {success}")
        time.sleep(test_delay)
    print("Automated test complete. Waiting briefly for final response data...")
    time.sleep(2.0)


def main():
    args = parse_args()
    monitor = SerialMonitor(
        port=args.port,
        baudrate=args.baud,
        timeout=args.timeout,
        raw_mode=args.raw,
        hex_mode=args.hex,
    )

    try:
        print(f"Opening serial port {args.port} at {args.baud} baud...")
        monitor.open()
        print("Serial port opened. Raw monitor is running.")
        print("Type commands and press Enter to send them. Type exit or quit to stop.")
        monitor.start_input_loop()

        if args.test:
            automated_test(monitor)
            monitor.stop_event.set()
        else:
            while not monitor.stop_event.is_set():
                time.sleep(0.1)
    except KeyboardInterrupt:
        monitor.stop_event.set()
    except SerialException as exc:
        sys.stderr.write(f"SERIAL ERROR: {exc}\n")
        monitor.exception = exc
    except Exception as exc:
        sys.stderr.write(f"UNEXPECTED ERROR: {type(exc).__name__}: {exc}\n")
        monitor.exception = exc
    finally:
        monitor.close()
        summary = monitor.get_summary()
        print_status(summary)


if __name__ == "__main__":
    main()
