"""
AgentTrace Benchmark Suite - Ed25519 Cryptographic Performance
Measures asymmetric Ed25519 signature generation and signature verification throughput (ops/sec and latency).
"""

import os
import statistics
import sys
import time
from typing import Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils import Ed25519KeyManager


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


def run_crypto_benchmark(warmup: int = 100, iterations: int = 1000) -> Dict[str, float]:
    """
    Methodology:
    - Generates key pair using Ed25519KeyManager.
    - Warm-up phase: Runs sign & verify operations to exercise OpenSSL / PyCA cryptography C bindings.
    - Measurement phase 1: Measures Ed25519 signing latency and throughput across `iterations`.
    - Measurement phase 2: Measures Ed25519 signature verification latency and throughput across `iterations`.
    """
    km = Ed25519KeyManager()
    sample_payload = "audit_session_proof_hash_manifest_019fc3e0_uuidv7_compliance_log_record"

    # Warm-up phase
    for _ in range(warmup):
        sig = km.sign(sample_payload)
        km.verify(sample_payload, sig)

    # 1. Measure Signing
    sign_durations_ms: List[float] = []
    signatures: List[str] = []

    for _ in range(iterations):
        t0 = time.perf_counter()
        sig = km.sign(sample_payload)
        t1 = time.perf_counter()
        sign_durations_ms.append((t1 - t0) * 1000)
        signatures.append(sig)

    # 2. Measure Verification
    verify_durations_ms: List[float] = []

    for i in range(iterations):
        sig = signatures[i]
        t0 = time.perf_counter()
        valid = km.verify(sample_payload, sig)
        t1 = time.perf_counter()
        assert valid, "Signature verification failed during benchmark"
        verify_durations_ms.append((t1 - t0) * 1000)

    sign_total_sec = sum(sign_durations_ms) / 1000.0
    verify_total_sec = sum(verify_durations_ms) / 1000.0

    return {
        "benchmark_name": "ed25519_crypto_performance",
        "warmup_iterations": warmup,
        "measurement_iterations": iterations,
        "sign_p50_ms": round(percentile(sign_durations_ms, 50), 6),
        "sign_p95_ms": round(percentile(sign_durations_ms, 95), 6),
        "sign_p99_ms": round(percentile(sign_durations_ms, 99), 6),
        "sign_mean_ms": round(statistics.mean(sign_durations_ms), 6),
        "sign_ops_per_sec": round(iterations / sign_total_sec, 2),
        "verify_p50_ms": round(percentile(verify_durations_ms, 50), 6),
        "verify_p95_ms": round(percentile(verify_durations_ms, 95), 6),
        "verify_p99_ms": round(percentile(verify_durations_ms, 99), 6),
        "verify_mean_ms": round(statistics.mean(verify_durations_ms), 6),
        "verify_ops_per_sec": round(iterations / verify_total_sec, 2)
    }


if __name__ == "__main__":
    print(run_crypto_benchmark())
