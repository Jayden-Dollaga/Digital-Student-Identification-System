import threading
from types import SimpleNamespace

import pytest

from gui_web import api as api_module


pytestmark = pytest.mark.unit


def test_concurrent_connect_calls_start_only_one_reader_thread(monkeypatch):
    real_thread = threading.Thread
    connect_barrier = threading.Barrier(2)
    start_barrier = threading.Barrier(2)
    first_reader_starting = threading.Event()
    release_first_start = threading.Event()
    release_reader_loop = threading.Event()
    second_liveness_check = threading.Event()
    readers = []
    readers_lock = threading.Lock()
    results = []
    failures = []

    monkeypatch.setattr(
        api_module,
        "load_settings",
        lambda: {"auto_detect_serial": False, "auto_reconnect": False},
    )
    monkeypatch.setattr(api_module, "save_settings", lambda settings: None)
    monkeypatch.setattr(api_module.permissions, "require_permission", lambda action: True)

    api = api_module.Api()
    api.serial.connected = True
    api.serial.esp32 = SimpleNamespace(is_open=True)
    api.serial.reconnect_port = "COM4"
    api.serial.reconnect_baud = 115200

    def serial_connect(**kwargs):
        connect_barrier.wait(timeout=5)
        return True, "OK"

    monkeypatch.setattr(api.serial, "connect", serial_connect)
    monkeypatch.setattr(api, "_push", lambda event, payload: None)
    monkeypatch.setattr(api, "request_fingerprint_count", lambda: True)

    def reader_loop():
        release_reader_loop.wait(timeout=5)

    monkeypatch.setattr(api, "_read_loop", reader_loop)
    original_start_read_loop = api._start_read_loop

    def synchronized_start_read_loop():
        start_barrier.wait(timeout=5)
        original_start_read_loop()

    monkeypatch.setattr(api, "_start_read_loop", synchronized_start_read_loop)

    class ControlledReaderThread:
        def __init__(self, target, daemon=None, name=None):
            self._thread = real_thread(target=target, daemon=daemon, name=name)

        def start(self):
            with readers_lock:
                readers.append(self)
                should_pause = len(readers) == 1
            if should_pause:
                first_reader_starting.set()
                if not release_first_start.wait(timeout=5):
                    raise RuntimeError("test did not release the first reader thread")
            self._thread.start()

        def is_alive(self):
            second_liveness_check.set()
            return self._thread.is_alive()

        def join(self, timeout=None):
            self._thread.join(timeout)

    monkeypatch.setattr(api_module.threading, "Thread", ControlledReaderThread)

    def connect_worker():
        try:
            results.append(api.connect(port="COM4", baud=115200, auto_detect=False))
        except BaseException as exc:
            failures.append(exc)

    connection_threads = [real_thread(target=connect_worker) for _ in range(2)]
    try:
        for thread in connection_threads:
            thread.start()

        assert first_reader_starting.wait(timeout=5)
        second_liveness_check.wait(timeout=1)
        release_first_start.set()

        for thread in connection_threads:
            thread.join(timeout=5)

        assert not any(thread.is_alive() for thread in connection_threads)
        assert not failures
        assert len(results) == 2
        assert all(result["connected"] for result in results)
        assert len(readers) == 1
    finally:
        release_first_start.set()
        release_reader_loop.set()
        for reader in readers:
            reader.join(timeout=2)
        for thread in connection_threads:
            thread.join(timeout=2)
        api_module.LOG.removeHandler(api._log_handler)