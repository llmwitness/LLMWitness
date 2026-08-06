"""
AgentTrace Benchmark Suite - SDK Queue Overhead
Measures Python SDK main-thread latency overhead when enqueueing telemetry events.
"""

import statistics
import time
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agenttrace_sdk import AgentTraceTracker
from utils import generate_uuidv7


def percentile(data: List[float], p: float) -> float:
    """Calculates percentile p (0-100) using linear interpolation."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return float(sorted_data[-1])
    d0 = sorted_data[f] * (c - k)
    d1 = sorted_data[c] * (k - f)
    return float(d0 + d1)


def run_sdk_queue_benchmark(warmup: int = 200, iterations: int = 2000, ingestion_url: str = "http://localhost:8000") -> Dict[str, float]:
    """
    Methodology:
    - Warm-up phase: Enqueues `warmup` events to initialize worker thread, queue allocation, and memory buffers.
    - Measurement phase: Measures high-resolution time (`perf_counter`) for `record_event()` main-thread calls.
    - Output: p50, p95, p99, mean, min, max latencies in milliseconds and microseconds.
    """
    tracker = AgentTraceTracker(ingestion_url=ingestion_url)
    cid = generate_uuidv7()

    # Warm-up phase
    for i in range(warmup):
        tracker.record_event(
            correlation_id=cid,
            task_name="warmup_task",
            prompt_tokens=10,
            completion_tokens=20,
            completion_string=f"Warmup payload {i}",
            agent_state={"step": i}
        )

    # Measurement phase
    durations_ms: List[float] = []
    for i in range(iterations):
        t0 = time.perf_counter()
        tracker.record_event(
            correlation_id=cid,
            task_name="benchmark_task",
            prompt_tokens=32,
            completion_tokens=64,
            completion_string=f"Measured event iteration {i} with payload data",
            tool_calls=[{"name": "query_db", "arguments": {"id": i}}],
            agent_state={"memory_step": i, "status": "active"}
        )
        t1 = time.perf_counter()
        durations_ms.append((t1 - t0) * 1000)

    tracker.flush()
    tracker.shutdown()

    p50_ms = percentile(durations_ms, 50)
    p95_ms = percentile(durations_ms, 95)
    p99_ms = percentile(durations_ms, 99)
    mean_ms = statistics.mean(durations_ms)

    return {
        "benchmark_name": "sdk_queue_overhead",
        "warmup_iterations": warmup,
        "measurement_iterations": iterations,
        "main_thread_p50_ms": round(p50_ms, 6),
        "main_thread_p95_ms": round(p95_ms, 6),
        "main_thread_p99_ms": round(p99_ms, 6),
        "main_thread_mean_ms": round(mean_ms, 6),
        "main_thread_p50_us": round(p50_ms * 1000, 2),
        "main_thread_p95_us": round(p95_ms * 1000, 2),
        "main_thread_p99_us": round(p99_ms * 1000, 2),
        "main_thread_mean_us": round(mean_ms * 1000, 2),
        "events_per_sec": round(iterations / (sum(durations_ms) / 1000.0), 2)
    }


if __name__ == "__main__":
    results = run_sdk_queue_benchmark()
    print("SDK Queue Benchmark Results:")
    print(results)
