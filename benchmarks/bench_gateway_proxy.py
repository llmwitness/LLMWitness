"""
AgentTrace Benchmark Suite - Gateway Latency & Proxy Overhead
Measures Gateway proxy response latency (p50, p95, p99) and proxy forwarding overhead.
"""

import os
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


def run_gateway_proxy_benchmark(
    gateway_url: str,
    warmup: int = 50,
    iterations: int = 500
) -> Dict[str, float]:
    """
    Methodology:
    - Sends warm-up HTTP POST requests to Gateway `/v1/chat/completions` endpoint.
    - Sends measurement requests with unique UUIDv7 correlation IDs.
    - Computes Gateway end-to-end request latencies and overhead distribution.
    """
    client = httpx.Client(timeout=10.0)
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": "Benchmark request payload to measure Gateway proxy overhead"}
        ]
    }

    # Warm-up phase
    for _ in range(warmup):
        cid = generate_uuidv7()
        try:
            client.post(
                f"{gateway_url}/v1/chat/completions",
                json=payload,
                headers={"X-AgentTrace-Correlation-ID": cid}
            )
        except Exception:
            pass

    # Measurement phase
    durations_ms: List[float] = []
    success_count = 0

    for _ in range(iterations):
        cid = generate_uuidv7()
        t0 = time.perf_counter()
        res = client.post(
            f"{gateway_url}/v1/chat/completions",
            json=payload,
            headers={"X-AgentTrace-Correlation-ID": cid}
        )
        t1 = time.perf_counter()
        if res.status_code == 200:
            durations_ms.append((t1 - t0) * 1000)
            success_count += 1

    client.close()

    p50 = percentile(durations_ms, 50)
    p95 = percentile(durations_ms, 95)
    p99 = percentile(durations_ms, 99)
    mean_lat = statistics.mean(durations_ms) if durations_ms else 0.0

    return {
        "benchmark_name": "gateway_proxy_overhead",
        "warmup_iterations": warmup,
        "measurement_iterations": iterations,
        "successful_requests": success_count,
        "gateway_p50_ms": round(p50, 4),
        "gateway_p95_ms": round(p95, 4),
        "gateway_p99_ms": round(p99, 4),
        "gateway_mean_ms": round(mean_lat, 4),
        "requests_per_sec": round(success_count / (sum(durations_ms) / 1000.0), 2) if durations_ms else 0.0
    }


if __name__ == "__main__":
    gw_url = os.getenv("GATEWAY_URL", "http://localhost:8011")
    print(run_gateway_proxy_benchmark(gateway_url=gw_url))
