"""Probe SerialWorker message handling during hardware diagnostics."""

import os
import sys
import time
from PySide6.QtCore import QCoreApplication, QTimer

sys.path.insert(0, os.path.join(os.getcwd(), "python"))
from core.serial_handler import SerialHandler
from core.attendance import AttendanceProcessor
from gui_qt.workers.serial_worker import SerialWorker


def main() -> None:
    app = QCoreApplication([])

    handler = SerialHandler()
    processor = AttendanceProcessor()
    worker = SerialWorker(handler, processor)

    def on_connection_changed(state: str) -> None:
        print(f"[SIGNAL] connection_changed: {state}")

    def on_mode_changed(mode: str) -> None:
        print(f"[SIGNAL] mode_changed: {mode}")

    def on_scan_event(event: dict) -> None:
        print(f"[SIGNAL] scan_event: {event}")

    def on_raw_line(line: str) -> None:
        print(f"[SIGNAL] raw_line: {repr(line)}")

    def on_enroll_progress(data: dict) -> None:
        print(f"[SIGNAL] enroll_progress: {data}")

    def on_wipe_progress(data: dict) -> None:
        print(f"[SIGNAL] wipe_progress: {data}")

    def on_error(msg: str) -> None:
        print(f"[SIGNAL] error: {msg}")

    worker.connection_changed.connect(on_connection_changed)
    worker.mode_changed.connect(on_mode_changed)
    worker.scan_event.connect(on_scan_event)
    worker.raw_line.connect(on_raw_line)
    worker.enroll_progress.connect(on_enroll_progress)
    worker.wipe_progress.connect(on_wipe_progress)
    worker.error.connect(on_error)

    worker.start()

    def start_connect() -> None:
        print("Connecting SerialHandler to COM4...")
        ok, msg = handler.connect("COM4", 115200, auto_detect=False)
        print(f"connect returned: {ok}, {msg}")
        if not ok:
            QTimer.singleShot(100, stop_and_exit)

    def stop_and_exit() -> None:
        print("Stopping worker and disconnecting...")
        worker.stop()
        handler.disconnect()
        app.quit()

    def send_probe_commands() -> None:
        print("Sending probe commands...")
        for cmd in ["LIST", "SCAN", "STOP"]:
            sent = handler.send_command(cmd)
            print(f"send_command({cmd}) -> {sent}")
            time.sleep(0.2)

    QTimer.singleShot(100, start_connect)
    QTimer.singleShot(2500, send_probe_commands)
    QTimer.singleShot(9000, stop_and_exit)

    app.exec()


if __name__ == "__main__":
    main()
