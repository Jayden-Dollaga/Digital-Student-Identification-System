"""Small optional profiler for timing CustomTkinter UI operations."""

import time
from collections import defaultdict

class PerfProfiler:
    def __init__(self, enabled=False, logger=None):
        self.enabled = enabled
        self.logger = logger
        self._starts = {}
        self._acc = defaultdict(float)
        self._counts = defaultdict(int)

    def start(self, key: str):
        if not self.enabled:
            return
        self._starts[key] = time.perf_counter()

    def stop(self, key: str):
        if not self.enabled or key not in self._starts:
            return
        elapsed = time.perf_counter() - self._starts.pop(key)
        self._acc[key] += elapsed
        self._counts[key] += 1

    def report(self):
        if not self.enabled:
            return
        lines = [f"Performance report (entries={len(self._acc)})"]
        for k, total in sorted(self._acc.items(), key=lambda it: -it[1]):
            cnt = self._counts.get(k, 0)
            avg = total / cnt if cnt else 0
            lines.append(f" - {k}: total={total:.4f}s count={cnt} avg={avg:.4f}s")
        text = "\n".join(lines)
        if self.logger:
            self.logger.info(text)
        else:
            print(text)

    def wrap(self, key: str):
        # simple context manager helper
        profiler = self
        class _Ctx:
            def __enter__(self):
                profiler.start(key)
            def __exit__(self, exc_type, exc, tb):
                profiler.stop(key)
        return _Ctx()
