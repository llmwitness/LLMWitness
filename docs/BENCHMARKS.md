# AgentTrace Benchmarking Methodology & Performance Engineering

This document details the benchmarking methodologies, target hardware environment, and metric calculation algorithms used to evaluate AgentTrace.

---

## 1. Target Benchmarking Environment

All performance benchmarks are designed and executed against the following target reference hardware:

- **CPU**: Intel Core Ultra 9 275HX (24 Cores / 24 Threads, up to 5.4 GHz)
- **RAM**: 32 GB DDR5
- **GPU**: NVIDIA GeForce RTX 5070 Mobile (8GB VRAM)
- **Storage**: 1 TB NVMe SSD
- **OS**: Ubuntu 24.04 LTS / WSL2 Linux

---

## 2. Statistical Methodology

### 2.1 Warm-up & Measurement Phases
To eliminate cold-start noise (Python bytecode compilation, JIT allocations, socket binding, OpenSSL key load), every benchmark performs explicit warm-up iterations prior to recording high-resolution timestamps.

### 2.2 Percentile Calculation
Percentiles ($p50, p95, p99$) are computed using linear interpolation:
$$k = (N - 1) \times \frac{p}{100}$$

Where $N$ represents total measurement iterations and $p$ represents target percentile rank.

---

## 3. Benchmark Targets

1. **SDK Queue Overhead**: Measures main-thread call latency for `record_event()`.
2. **Gateway Latency**: End-to-end response time percentiles for proxying chat requests.
3. **Ed25519 Signing & Verification**: Throughput (ops/sec) for asymmetric key operations.
4. **PII Engine Throughput**: Deep-JSON regex redaction operations per second and MB/sec.
5. **State-Aware Cache**: Latency comparison between cache miss and hit paths.
6. **Concurrency & Soak**: Stability and memory footprint under multi-threaded load over time.

---

## 4. Execution Command

Run the complete benchmark suite:
```bash
python benchmarks/run_benchmarks.py
```

Outputs are automatically saved to `benchmark_results.json`, `benchmark_results.csv`, and `BENCHMARK_REPORT.md`.
