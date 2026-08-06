"""
AgentTrace Benchmark Suite - PII Engine Throughput & Large Payloads
Measures inline deep-JSON and multi-modal PII redaction throughput (ops/sec, MB/sec, latencies)
across standard and scaled large payloads (up to 10MB).
"""

import json
import os
import statistics
import sys
import time
from typing import Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils import redact_payload


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


def generate_large_payload(size_kb: int = 1024) -> Dict:
    """Generates synthetic deep nested JSON structure with PII elements of given size in KB."""
    items = []
    base_item = {
        "user_id": 1024,
        "ssn": "123-45-6789",
        "credit_card": "4111-2222-3333-4444",
        "api_token": "sk-abcdef1234567890abcdef1234567890",
        "nested_meta": json.dumps({"internal_ssn": "987-65-4321", "auth_bearer": "Bearer token12345678901234567890"}),
        "safe_text": "Standard non-PII operational message context for compliance auditing."
    }
    
    # Calculate count needed to approximate size_kb
    single_size = len(json.dumps(base_item).encode("utf-8"))
    count = max(1, (size_kb * 1024) // single_size)
    
    for i in range(count):
        item = dict(base_item)
        item["record_index"] = i
        items.append(item)
        
    return {"batch_id": "large_payload_batch_001", "records": items}


def run_pii_benchmark(
    warmup: int = 100,
    standard_iterations: int = 1000,
    large_payload_size_kb: int = 1024,
    large_iterations: int = 20
) -> Dict[str, float]:
    """
    Methodology:
    - Standard test payload: Multi-PII JSON dictionary with embedded JSON string and token patterns.
    - Large test payload: Dynamically generated deep dictionary structure of `large_payload_size_kb` KB.
    - Warm-up phase: Executes redaction to prime regex engine compilation caches.
    - Measurement phase: Collects high-resolution timings for standard and large payload processing.
    """
    standard_payload = {
        "user_id": 999,
        "ssn": "123-45-6789",
        "card": "4532-1111-2222-3333",
        "token": "sk-abcdef1234567890abcdef1234567890",
        "metadata": json.dumps({"embedded_ssn": "987-65-4321", "safe_code": "ALLOW_ME_999"}),
        "note": "Standard compliance benchmark prompt payload."
    }
    
    # Warm-up phase
    for _ in range(warmup):
        redact_payload(standard_payload, allow_list=["ALLOW_ME_999"])

    # 1. Standard Payload Benchmark
    std_durations_ms: List[float] = []
    std_bytes = len(json.dumps(standard_payload).encode("utf-8"))

    for _ in range(standard_iterations):
        t0 = time.perf_counter()
        _ = redact_payload(standard_payload, allow_list=["ALLOW_ME_999"])
        t1 = time.perf_counter()
        std_durations_ms.append((t1 - t0) * 1000)

    std_total_sec = sum(std_durations_ms) / 1000.0
    std_ops_sec = standard_iterations / std_total_sec
    std_mb_sec = (std_bytes * standard_iterations / (1024 * 1024)) / std_total_sec

    # 2. Large Payload Benchmark
    large_payload = generate_large_payload(size_kb=large_payload_size_kb)
    large_bytes = len(json.dumps(large_payload).encode("utf-8"))
    large_durations_ms: List[float] = []

    for _ in range(large_iterations):
        t0 = time.perf_counter()
        _ = redact_payload(large_payload)
        t1 = time.perf_counter()
        large_durations_ms.append((t1 - t0) * 1000)

    large_total_sec = sum(large_durations_ms) / 1000.0
    large_ops_sec = large_iterations / large_total_sec
    large_mb_sec = (large_bytes * large_iterations / (1024 * 1024)) / large_total_sec

    return {
        "benchmark_name": "pii_throughput_and_large_payloads",
        "standard_payload_size_bytes": std_bytes,
        "standard_iterations": standard_iterations,
        "standard_p50_ms": round(percentile(std_durations_ms, 50), 6),
        "standard_p95_ms": round(percentile(std_durations_ms, 95), 6),
        "standard_p99_ms": round(percentile(std_durations_ms, 99), 6),
        "standard_mean_ms": round(statistics.mean(std_durations_ms), 6),
        "standard_ops_per_sec": round(std_ops_sec, 2),
        "standard_throughput_mb_s": round(std_mb_sec, 2),
        "large_payload_size_kb": round(large_bytes / 1024, 2),
        "large_iterations": large_iterations,
        "large_p50_ms": round(percentile(large_durations_ms, 50), 4),
        "large_p95_ms": round(percentile(large_durations_ms, 95), 4),
        "large_p99_ms": round(percentile(large_durations_ms, 99), 4),
        "large_mean_ms": round(statistics.mean(large_durations_ms), 4),
        "large_throughput_mb_s": round(large_mb_sec, 2)
    }


if __name__ == "__main__":
    print(run_pii_benchmark())
