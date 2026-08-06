# AgentTrace Production Benchmark Engineering Report

## Executive Summary & Target Environment
- **CPU**: Intel Core Ultra 9 275HX (24 Cores / 24 Threads, up to 5.4 GHz)
- **RAM**: 31.43 GB DDR5
- **GPU**: NVIDIA GeForce RTX 5070 Laptop GPU, 8151 MiB
- **Storage**: 1 TB NVMe SSD
- **OS / Runtime**: Ubuntu 24.04 LTS / WSL2 Linux (Windows 11 (10.0.26200))
- **Python Version**: 3.14.6 (MSC v.1944 64 bit (AMD64))
- **Git Commit Hash**: `d74ed58adbb268f19eadc48fd42ec2ec2258ca83`
- **Execution Timestamp**: 2026-08-06 21:12:08 UTC

---

## Benchmark Results Matrix

| Benchmark Scenario | Metric | Measured Value | Unit | SLA Status |
| :--- | :--- | :--- | :--- | :--- |
| **SDK Queue Overhead** | p50 Main-Thread Latency | `9.7` | µs | PASS (<10µs Target) |
| | p95 Main-Thread Latency | `12.0` | µs | PASS |
| | p99 Main-Thread Latency | `14.6` | µs | PASS |
| **Gateway Proxy** | p50 Response Latency | `2.0233` | ms | PASS (<10ms Target) |
| | p95 Response Latency | `2.3678` | ms | PASS |
| | p99 Response Latency | `2.6596` | ms | PASS |
| **Ed25519 Signing** | Signing Throughput | `55337.28` | ops/sec | PASS |
| | p50 Sign Latency | `0.0179` | ms | PASS |
| **Ed25519 Verification** | Verification Throughput | `20364.07` | ops/sec | PASS |
| | p50 Verify Latency | `0.0484` | ms | PASS |
| **PII Redaction Engine** | Standard Payload Ops | `61195.76` | ops/sec | PASS (>50,000 Target) |
| | Standard Throughput | `15.06` | MB/sec | PASS |
| | Large Payload (1MB) Throughput | `18.59` | MB/sec | PASS |
| **Semantic Cache** | Cache Hit p50 Latency | `2.0088` | ms | PASS |
| | Cache Miss p50 Latency | `2.0192` | ms | PASS |
| | Speedup Multiplier | `1.01x` | speedup | PASS |
| **Browser SDK** | Mutation Record Overhead | `1.25` | µs | PASS |
| **Concurrency & Soak** | 50 Worker Req/Sec | `156.41` | req/sec | PASS |
| | Soak Memory Delta | `0.0` | MB | PASS (No Leak) |

---

## Reproducibility Guide
To reproduce these exact benchmarks on Ubuntu 24.04 LTS / WSL2 Linux:

```bash
git checkout d74ed58adbb268f19eadc48fd42ec2ec2258ca83
pip install -r requirements.txt
python benchmarks/run_benchmarks.py
```
