# Local benchmarks

Run the benchmark harness from a source checkout:

```bash
python -m benchmarks.benchmark_local --iterations 1000 --warmup 100
```

To retain raw JSON locally:

```bash
python -m benchmarks.benchmark_local --output benchmark_results.local.json
```

The output records the commit, timestamp, Python runtime, operating system, logical CPU count, workload size, sample count, warmup count, and latency distribution. Results describe only that run and are not service-level objectives, production capacity claims, or comparisons with other products.
