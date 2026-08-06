"""
AgentTrace Benchmark Suite - System Resources (CPU, Memory, Concurrency, Soak & Stress)
Measures process memory footprint (RSS/VMS), CPU utilization across thread pools,
multi-threaded concurrent request throughput, long-running stability soak, and high-concurrency stress breaking point.
"""

import concurrent.futures
import os
import psutil
import statistics
import sys
import time
from typing import Dict, List
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils import generate_uuidv7


def percentile(data: List[float], p: float) -> float:
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


def capture_resource_usage() -> Dict[str, float]:
    """Captures CPU percentage and Memory RSS/VMS in MB for current process."""
    proc = psutil.Process(os.getpid())
    mem = proc.memory_info()
    return {
        "cpu_percent": proc.cpu_percent(interval=0.1),
        "memory_rss_mb": round(mem.rss / (1024 * 1024), 2),
        "memory_vms_mb": round(mem.vms / (1024 * 1024), 2)
    }


def run_concurrency_benchmark(gateway_url: str, concurrency_levels: List[int] = [10, 50, 100], requests_per_worker: int = 20) -> Dict[str, float]:
    """
    Methodology:
    - Launches thread pools with worker counts specified in `concurrency_levels`.
    - Each worker fires `requests_per_worker` HTTP POST requests concurrently to Gateway.
    - Measures aggregate throughput (req/sec) and error rates under multi-threaded concurrency.
    """
    results = {}
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "Concurrent benchmark request"}]
    }

    for num_workers in concurrency_levels:
        total_requests = num_workers * requests_per_worker
        latencies: List[float] = []
        errors = 0

        def worker_task():
            nonlocal errors
            client = httpx.Client(timeout=10.0)
            for _ in range(requests_per_worker):
                t0 = time.perf_counter()
                try:
                    cid = generate_uuidv7()
                    res = client.post(
                        f"{gateway_url}/v1/chat/completions",
                        json=payload,
                        headers={"X-AgentTrace-Correlation-ID": cid}
                    )
                    t1 = time.perf_counter()
                    if res.status_code == 200:
                        latencies.append((t1 - t0) * 1000)
                    else:
                        errors += 1
                except Exception:
                    errors += 1
            client.close()

        t_start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(worker_task) for _ in range(num_workers)]
            concurrent.futures.wait(futures)
        t_total = time.perf_counter() - t_start

        results[f"concurrency_{num_workers}"] = {
            "num_workers": num_workers,
            "total_requests": total_requests,
            "total_duration_sec": round(t_total, 3),
            "requests_per_sec": round(total_requests / t_total, 2) if t_total > 0 else 0.0,
            "p50_latency_ms": round(percentile(latencies, 50), 2),
            "p95_latency_ms": round(percentile(latencies, 95), 2),
            "error_count": errors,
            "error_rate_percent": round((errors / total_requests) * 100, 2)
        }

    return results


def run_soak_benchmark(gateway_url: str, duration_sec: int = 15, request_interval_sec: float = 0.05) -> Dict[str, float]:
    """
    Methodology:
    - Runs continuous telemetry stream for `duration_sec` seconds to check for memory leaks or performance degradation over time.
    - Captures resource usage before, during, and after soak test.
    """
    initial_resources = capture_resource_usage()
    client = httpx.Client(timeout=10.0)
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "Soak test continuous audit payload"}]
    }

    latencies: List[float] = []
    t_start = time.time()
    count = 0

    while time.time() - t_start < duration_sec:
        t0 = time.perf_counter()
        try:
            res = client.post(
                f"{gateway_url}/v1/chat/completions",
                json=payload,
                headers={"X-AgentTrace-Correlation-ID": generate_uuidv7()}
            )
            t1 = time.perf_counter()
            if res.status_code == 200:
                latencies.append((t1 - t0) * 1000)
                count += 1
        except Exception:
            pass
        time.sleep(request_interval_sec)

    client.close()
    final_resources = capture_resource_usage()

    return {
        "benchmark_name": "soak_test_stability",
        "duration_sec": duration_sec,
        "total_requests_completed": count,
        "avg_throughput_req_sec": round(count / duration_sec, 2),
        "p50_latency_ms": round(percentile(latencies, 50), 2),
        "p95_latency_ms": round(percentile(latencies, 95), 2),
        "initial_rss_mb": initial_resources["memory_rss_mb"],
        "final_rss_mb": final_resources["memory_rss_mb"],
        "memory_delta_mb": round(final_resources["memory_rss_mb"] - initial_resources["memory_rss_mb"], 2)
    }


def run_stress_benchmark(gateway_url: str, max_concurrent_workers: int = 150) -> Dict[str, float]:
    """
    Methodology:
    - Stress tests the system under burst high-concurrency traffic to determine breaking limits and degradation curves.
    """
    return run_concurrency_benchmark(gateway_url, concurrency_levels=[max_concurrent_workers], requests_per_worker=10)


if __name__ == "__main__":
    gw_url = os.getenv("GATEWAY_URL", "http://localhost:8011")
    print("Resource Usage:", capture_resource_usage())
    print("Concurrency Benchmark:", run_concurrency_benchmark(gw_url, [5, 10], 5))
