"""Optional lightweight timing profiler for the V3 web/API layer."""

import time
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Optional


class PerfProfiler:
    """Collect named elapsed-time measurements when explicitly enabled."""

    def __init__(self, enabled: bool = False, logger: Optional[Any] = None) -> None:
        self.enabled = enabled
        self.logger = logger
        self._starts: Dict[str, float] = {}
        self._acc: DefaultDict[str, float] = defaultdict(float)
        self._counts: DefaultDict[str, int] = defaultdict(int)

    def start(self, key: str) -> None:
        if not self.enabled:
            return
        self._starts[key] = time.perf_counter()

    def stop(self, key: str) -> None:
        if not self.enabled or key not in self._starts:
            return
        elapsed = time.perf_counter() - self._starts.pop(key)
        self._acc[key] += elapsed
        self._counts[key] += 1

    def report(self) -> None:
        if not self.enabled:
            return
        lines: List[str] = [f"Performance report (entries={len(self._acc)})"]
        for key, total in sorted(self._acc.items(), key=lambda item: -item[1]):
            count = self._counts.get(key, 0)
            average = total / count if count else 0
            lines.append(
                f" - {key}: total={total:.4f}s count={count} avg={average:.4f}s"
            )
        text = "\n".join(lines)
        if self.logger:
            self.logger.info(text)
        else:
            print(text)

    def wrap(self, key: str):
        profiler = self

        class _Context:
            def __enter__(self):
                profiler.start(key)
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                profiler.stop(key)

        return _Context()
