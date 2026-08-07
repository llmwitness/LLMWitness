# Python SDK reference

```python
from llmwitness import LLMWitnessTracker, trace_session
```

`LLMWitnessTracker.record_event(...)` queues a scrubbed telemetry event without waiting for network delivery. A full queue increments `dropped_events`. A failed HTTP delivery increments `delivery_failures`. Neither condition is retried durably.

`tracker.flush()` waits for the current queue to be processed and can therefore wait on configured HTTP timeouts. `tracker.shutdown(timeout_sec=15)` requests worker shutdown and returns whether the worker stopped within the timeout.

`trace_session(task_name, correlation_id=None)` binds a UUIDv7 correlation ID through Python context variables. UUIDv7 is for correlation, not authorization or replay protection.

`llmwitness verify RECEIPT --trusted-fingerprint SHA256_HEX` verifies the receipt signature and requires the embedded signing-key fingerprint to match a value obtained through a trusted channel. Without this option, signature verification proves only internal consistency with the key embedded in the receipt.
