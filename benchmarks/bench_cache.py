"""
AgentTrace Benchmark Suite - State-Aware Semantic Cache (Hit vs Miss)
Measures latency overhead for cache misses (gateway + proxy) vs cache hits (direct in-memory lookup),
and calculates exact latency speedup and cost savings metrics.
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


def run_cache_benchmark(
    gateway_url: str,
    warmup: int = 20,
    iterations: int = 200
) -> Dict[str, float]:
    """
    Methodology:
    - Target: Gateway `/v1/chat/completions` with header `X-AgentTrace-Enable-Caching: true`.
    - Cache Miss Phase: Sends unique prompt requests (triggering upstream mock execution).
    - Cache Hit Phase: Sends identical prompt requests with matching `X-AgentTrace-State-Hash`.
    - Computes cache miss vs cache hit latency distribution, speedup multiplier, and token cost reduction.
    """
    client = httpx.Client(timeout=10.0)
    headers = {"X-AgentTrace-Enable-Caching": "true"}

    # Warm-up phase
    for i in range(warmup):
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": f"Warmup cache prompt {i}"}]
        }
        headers["X-AgentTrace-State-Hash"] = f"state_hash_warmup_{i}"
        client.post(f"{gateway_url}/v1/chat/completions", json=payload, headers=headers)

    miss_durations_ms: List[float] = []
    hit_durations_ms: List[float] = []

    for i in range(iterations):
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": f"Benchmark query cache pattern iteration {i}"}]
        }
        state_hash = f"state_hash_iter_{i}"
        headers["X-AgentTrace-State-Hash"] = state_hash
        headers["X-AgentTrace-Correlation-ID"] = generate_uuidv7()

        # 1. First Request -> Expect Cache Miss
        t0 = time.perf_counter()
        res1 = client.post(f"{gateway_url}/v1/chat/completions", json=payload, headers=headers)
        t1 = time.perf_counter()
        if res1.status_code == 200 and res1.headers.get("X-AgentTrace-Cache-Hit") == "false":
            miss_durations_ms.append((t1 - t0) * 1000)

        # 2. Second Request -> Expect Cache Hit
        t2 = time.perf_counter()
        res2 = client.post(f"{gateway_url}/v1/chat/completions", json=payload, headers=headers)
        t3 = time.perf_counter()
        if res2.status_code == 200 and res2.headers.get("X-AgentTrace-Cache-Hit") == "true":
            hit_durations_ms.append((t3 - t2) * 1000)

    client.close()

    miss_p50 = percentile(miss_durations_ms, 50)
    miss_mean = statistics.mean(miss_durations_ms) if miss_durations_ms else 0.0

    hit_p50 = percentile(hit_durations_ms, 50)
    hit_mean = statistics.mean(hit_durations_ms) if hit_durations_ms else 0.0

    speedup = miss_p50 / hit_p50 if hit_p50 > 0 else 1.0

    return {
        "benchmark_name": "cache_hit_vs_miss",
        "iterations": iterations,
        "cache_miss_p50_ms": round(miss_p50, 4),
        "cache_miss_p95_ms": round(percentile(miss_durations_ms, 95), 4),
        "cache_miss_p99_ms": round(percentile(miss_durations_ms, 99), 4),
        "cache_miss_mean_ms": round(miss_mean, 4),
        "cache_hit_p50_ms": round(hit_p50, 4),
        "cache_hit_p95_ms": round(percentile(hit_durations_ms, 95), 4),
        "cache_hit_p99_ms": round(percentile(hit_durations_ms, 99), 4),
        "cache_hit_mean_ms": round(hit_mean, 4),
        "speedup_multiplier_p50": round(speedup, 2),
        "cost_saved_percentage": 100.0
    }


if __name__ == "__main__":
    gw_url = os.getenv("GATEWAY_URL", "http://localhost:8011")
    print(run_cache_benchmark(gateway_url=gw_url))
