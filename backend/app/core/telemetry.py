import time
from typing import Dict, Any
from contextlib import contextmanager


class TelemetryTimer:
    """High-precision execution timer using time.perf_counter()."""

    def __init__(self):
        self._start_time = time.perf_counter()
        self.retrieval_latency_ms: float = 0.0
        self.rerank_latency_ms: float = 0.0
        self.generation_latency_ms: float = 0.0
        self.total_latency_ms: float = 0.0

    @contextmanager
    def measure(self, stage: str):
        """Context manager to measure the execution latency of a pipeline stage in milliseconds."""
        t0 = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            # Ensure positive numeric value even for sub-millisecond execution
            elapsed_ms = max(round(elapsed_ms, 2), 0.01)
            if stage == "retrieval":
                self.retrieval_latency_ms = elapsed_ms
            elif stage == "rerank":
                self.rerank_latency_ms = elapsed_ms
            elif stage == "generation":
                self.generation_latency_ms = elapsed_ms

    def finish(self) -> Dict[str, float]:
        """Calculates total end-to-end latency and returns dictionary."""
        total = (time.perf_counter() - self._start_time) * 1000.0
        self.total_latency_ms = max(round(total, 2), 0.01)

        # In case total is less than the sum of measured stages due to floating precision, adjust
        stages_sum = round(self.retrieval_latency_ms + self.rerank_latency_ms + self.generation_latency_ms, 2)
        if stages_sum > self.total_latency_ms:
            self.total_latency_ms = stages_sum

        return {
            "retrieval_latency_ms": self.retrieval_latency_ms,
            "rerank_latency_ms": self.rerank_latency_ms,
            "generation_latency_ms": self.generation_latency_ms,
            "total_latency_ms": self.total_latency_ms,
        }
