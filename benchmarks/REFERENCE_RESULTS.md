# LLMWitness local benchmark reference

This report is a reproducible development reference for LLMWitness Community. It is not an SLA, a production-capacity result, a comparison with another product, or evidence of network/model-provider performance.

## Recorded environment

| Field | Value |
| --- | --- |
| Commit | `ddb2cd5ef6ddbe8ce7e6110873541b9420634b22` |
| Worktree | Clean |
| Timestamp | `2026-08-11T21:18:33Z` |
| Python | 3.14.6, 64-bit CPython |
| Platform | Windows 11 (`10.0.26200`) |
| Processor identifier | Intel64 Family 6 Model 198 Stepping 2, GenuineIntel |
| Logical CPUs | 24 |
| fastapi | 0.141.1 |
| httpx | 0.28.1 |
| pydantic | 2.13.4 |
| cryptography | 50.0.0 |

## Method

- Clock: `time.perf_counter_ns`
- Samples per case: 1,000
- Warmup iterations per case: 100
- Process model: one local Python process
- Percentiles: nearest-rank observation from sorted samples
- Spread: sample standard deviation
- Units: microseconds per measured operation

The SDK case measures synchronous `record_event` work and bounded-queue insertion while a local stub accepts worker deliveries. The gateway case uses FastAPI in-process through `httpx.ASGITransport`, a deterministic mock upstream, and a mock successful telemetry endpoint. Neither case includes internet or model-provider latency.

## Results

| Case | Mean | Std dev | p50 | p90 | p95 | p99 | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `sdk_record_event` | 5.979 | 7.040 | 5.3 | 6.1 | 6.6 | 15.2 | 4.8 | 164.6 |
| `redact_payload` | 9.380 | 1.074 | 9.3 | 9.8 | 10.1 | 14.7 | 8.1 | 24.1 |
| `ed25519_sign` | 19.357 | 20.938 | 18.2 | 19.3 | 23.3 | 31.7 | 16.7 | 668.3 |
| `ed25519_verify` | 50.157 | 6.202 | 49.5 | 53.3 | 55.1 | 66.4 | 44.6 | 169.6 |
| `mock_gateway_request` | 631.295 | 79.371 | 607.6 | 708.1 | 812.7 | 939.5 | 551.0 | 1,391.2 |

The redaction input was 168 UTF-8 bytes and contains one SSN-shaped value, one payment-card-shaped value, one bearer-token-shaped value, and a short message. The SDK run reported zero dropped events and zero delivery failures under this specific stubbed workload.

## Interpretation and limitations

- Tail percentiles are more representative than the maximum for this run; isolated scheduling and runtime outliers are retained rather than removed.
- The cases are microbenchmarks, not end-to-end production tests.
- No sustained throughput, concurrency scaling, memory growth, disk durability, external network, model-provider, or multi-user behavior is measured.
- Pattern-scrubbing latency depends strongly on payload size, nesting, content, and configured allow-list entries.
- Results can change with power settings, background activity, Python/dependency versions, operating system, and hardware.
- Rerun the harness on the intended deployment system before making performance decisions.

The complete machine-readable result is available in [`results/windows-python314-ddb2cd5.json`](results/windows-python314-ddb2cd5.json).
