# AgentTrace SDK Reference

This document provides complete class and method reference for the Python SDK (`agenttrace_sdk.py`) and JavaScript Browser SDK (`agenttrace.js`).

---

## 1. Python SDK Reference (`agenttrace_sdk.py`)

### `class AgentTraceTracker`

The core telemetry recorder managing background daemon queues.

#### Constructor:
```python
tracker = AgentTraceTracker(
    ingestion_url: str = "http://localhost:8000",
    max_queue_size: int = 10000,
    batch_size: int = 50,
    flush_interval_sec: float = 1.0
)
```

#### Context Manager Methods:
```python
with tracker.trace_session(task_name: str, correlation_id: Optional[str] = None) as cid:
    # Code executing within session...
```
- `task_name`: Logical string identifier for task context.
- `correlation_id`: Optional explicit RFC 9562 UUIDv7 string. Auto-generated if omitted.

#### Event Recording:
```python
tracker.record_event(
    correlation_id: Optional[str] = None,
    task_name: Optional[str] = None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    completion_string: str = "",
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    agent_state: Optional[Dict[str, Any]] = None
) -> None
```
Enqueues telemetry payload onto internal non-blocking queue. Main-thread execution returns immediately.

#### Queue Management:
- `tracker.flush()`: Blocks until all pending queued events are dispatched to ingestion service.
- `tracker.shutdown()`: Signals worker thread termination and flushes pending queue items.

---

## 2. JavaScript Browser SDK Reference (`agenttrace.js`)

### `class AgentTraceBrowserSDK`

Client-side browser telemetry recorder tracking DOM mutations.

#### Constructor:
```javascript
const sdk = new AgentTraceBrowserSDK({
    endpoint: "http://localhost:8000/ingest",
    batchSize: 20,
    flushIntervalMs: 2000
});
```

#### Methods:
- `sdk.recordMutation(eventType: string, details: string|object)`: Enqueues DOM mutation record.
- `sdk.flush()`: Dispatches batched events via `fetch` API.
