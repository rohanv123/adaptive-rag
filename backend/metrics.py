# metrics.py
# Responsibility: Track request latencies and compute percentile stats.
# Also separate retrieval time from generation time.

import time
import statistics
from dataclasses import dataclass, field


@dataclass
class LatencyRecord:
    total_ms:      float
    retrieval_ms:  float
    generation_ms: float
    top_k:         int
    strategy:      str
    timestamp:     float = field(default_factory=time.time)


class MetricsTracker:
    """
    Stores latency records and computes statistics.
    Keeps last 1000 records in memory (enough for meaningful percentiles).
    """
    def __init__(self, max_records: int = 1000):
        self.records: list[LatencyRecord] = []
        self.max_records = max_records

    def record(self, total_ms: float, retrieval_ms: float,
               generation_ms: float, top_k: int, strategy: str):
        rec = LatencyRecord(
            total_ms=total_ms,
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms,
            top_k=top_k,
            strategy=strategy
        )
        self.records.append(rec)
        if len(self.records) > self.max_records:
            self.records.pop(0)   # drop oldest record

    def _percentile(self, values: list[float], p: float) -> float:
        """Compute the p-th percentile of a list."""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = int(len(sorted_vals) * p / 100)
        idx = min(idx, len(sorted_vals) - 1)
        return round(sorted_vals[idx], 1)

    def report(self) -> dict:
        """Full stats report for the /metrics endpoint."""
        if not self.records:
            return {"message": "No queries yet.", "count": 0}

        totals      = [r.total_ms      for r in self.records]
        retrievals  = [r.retrieval_ms  for r in self.records]
        generations = [r.generation_ms for r in self.records]

        # Strategy breakdown
        strategy_counts = {}
        for r in self.records:
            strategy_counts[r.strategy] = strategy_counts.get(r.strategy, 0) + 1

        # K distribution
        k_values = [r.top_k for r in self.records]

        return {
            "count":   len(self.records),

            "total_latency": {
                "p50_ms": self._percentile(totals, 50),
                "p95_ms": self._percentile(totals, 95),
                "mean_ms": round(statistics.mean(totals), 1),
                "max_ms":  round(max(totals), 1),
                "min_ms":  round(min(totals), 1),
            },

            "retrieval_latency": {
                "p50_ms": self._percentile(retrievals, 50),
                "p95_ms": self._percentile(retrievals, 95),
                "mean_ms": round(statistics.mean(retrievals), 1),
            },

            "generation_latency": {
                "p50_ms": self._percentile(generations, 50),
                "p95_ms": self._percentile(generations, 95),
                "mean_ms": round(statistics.mean(generations), 1),
            },

            "strategy_counts":    strategy_counts,
            "avg_k":              round(statistics.mean(k_values), 2),

            # Recent history for sparkline charts in UI
            "recent_50": [
                {
                    "total_ms":     r.total_ms,
                    "retrieval_ms": r.retrieval_ms,
                    "top_k":        r.top_k,
                    "strategy":     r.strategy
                }
                for r in self.records[-50:]
            ]
        }


# Global singleton
_tracker = MetricsTracker()


class Timer:
    """Context manager for timing code blocks."""
    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000

    @property
    def ms(self) -> float:
        return self.elapsed_ms


def get_tracker() -> MetricsTracker:
    return _tracker