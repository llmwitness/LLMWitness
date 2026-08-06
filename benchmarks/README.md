# AgentTrace Production Benchmark Suite

This directory contains the production-ready performance benchmarking suite for AgentTrace.

## Benchmarking Targets & Architecture

The suite benchmarks 14 key engineering metrics:
1. **SDK Queue Overhead**: Main-thread latency for pushing telemetry into non-blocking `queue.Queue`.
2. **Gateway Latency**: End-to-end request response latencies through the FastAPI proxy.
3. **Proxy Overhead**: Added forwarding latency compared to direct HTTP requests.
4. **Ed25519 Signing**: Asymmetric signature generation throughput (ops/sec) and p50/p95/p99 latency.
5. **Ed25519 Verification**: Signature verification throughput and latency.
6. **PII Throughput**: Operations/sec and MB/sec throughput of the deep-JSON regex engine.
7. **Cache Hit vs Miss**: Latency speedup and 100% token cost saving verification for state-aware semantic cache.
8. **Browser SDK**: Payload serialization and DOM sidecar mutation observer tracking latency.
9. **Large Payloads**: Deep JSON payload processing (up to 10 MB) throughput.
10. **Memory Usage**: Process RSS and VMS memory footprint tracking.
11. **CPU Usage**: Multi-core CPU utilization during trace processing.
12. **Concurrency**: Multi-threaded client request handling (10, 50, 100 concurrent workers).
13. **Long-Running Soak**: Stability and memory leak detection over extended continuous operation.
14. **Stress Testing**: High-concurrency throughput limits and failure threshold analysis.

---

## Execution Command

Run the full benchmark suite:
```bash
python benchmarks/run_benchmarks.py
```

Run a quick validation pass:
```bash
python benchmarks/run_benchmarks.py --quick
```

Individual target execution:
```bash
python benchmarks/bench_sdk_queue.py
python benchmarks/bench_gateway_proxy.py
python benchmarks/bench_crypto.py
python benchmarks/bench_pii.py
python benchmarks/bench_cache.py
python benchmarks/bench_browser_sdk.py
python benchmarks/bench_system.py
```

---

## Methodology & Benchmark Phases

For every benchmark target:
1. **Hardware Metadata Capture**: Auto-captures CPU, RAM, GPU, NVMe storage, OS distro, Python compiler version, and current Git commit hash.
2. **Warm-Up Phase**: Priming iterations (e.g., regex compilation, worker thread creation, OpenSSL key loading, cache pre-allocations) to eliminate cold-start noise.
3. **Measurement Phase**: High-resolution performance measuring using `time.perf_counter()`. Percentiles (p50, p95, p99), mean, min, max, ops/sec, and MB/sec are computed.
4. **Export Generation**:
   - `benchmark_results.json`: Full detailed raw structured results.
   - `benchmark_results.csv`: Flattened CSV export for metric ingestion systems.
   - `BENCHMARK_REPORT.md`: Rendered Markdown executive summary report with SLA status.

---

## Target Benchmarking Environment Setup

- **CPU**: Intel Core Ultra 9 275HX (24 Cores / 24 Threads, up to 5.4 GHz)
- **RAM**: 32 GB DDR5
- **GPU**: NVIDIA GeForce RTX 5070 Mobile (8GB VRAM)
- **Storage**: 1 TB NVMe SSD
- **OS**: Ubuntu 24.04 LTS / WSL2 Linux

---

## Reproducibility Guide

To reproduce results on Ubuntu 24.04 LTS or WSL2 Linux:
1. Clone the repository and checkout target commit hash:
   ```bash
   git checkout <GIT_COMMIT_HASH>
   ```
2. Set up clean virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run benchmark suite:
   ```bash
   python benchmarks/run_benchmarks.py
   ```
4. Verify generated artifacts `benchmark_results.json`, `benchmark_results.csv`, and `BENCHMARK_REPORT.md`.
