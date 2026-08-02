# AgentTrace

> **Enterprise-Grade Cryptographic Audit Engine for Autonomous AI Agents**

AgentTrace provides end-to-end, tamper-evident audit logging for multi-agent workflows across server-side SDKs, proxy gateways, and client-side browser sidecars. All interaction vectors are correlated in real time using a unified **UUIDv7 Correlation ID**.

---

## 🚀 Architecture Overview

```
                      +----------------------------------+
                      |   Autonomous AI Agent App        |
                      +----------------------------------+
                                        |
                 +----------------------+----------------------+
                 |                                             |
                 v                                             v
   +---------------------------+                 +---------------------------+
   | AgentTrace Python SDK     |                 | Proxy Gateway             |
   | (agenttrace_sdk.py)       |                 | (gateway.py)              |
   | - Non-blocking Thread Queue|                 | - Sub-10ms ASGI Proxy     |
   | - trace_session(task)     |                 | - PII Scrubbing (Regex)   |
   | - UUIDv7 Correlation ID   |                 | - HMAC-SHA256 Signatures  |
   +-------------+-------------+                 +-------------+-------------+
                 |                                             |
                 |       +-----------------------------+       |
                 +------>| Immutable Ingestion Vault   |<------+
                         | (ingest.py)                 |
                 +------>| - WORM Storage Engine       |<------+
                 |       | - Sealed Session Manifests  |       |
                 |       +--------------+--------------+       |
                 |                      |                      |
   +-------------+-------------+        v        +-------------+-------------+
   | Chrome Auditor Extension  |  proof.json     | Cryptographic Proof       |
   | (content.js, bg.js)       |                 | Verification              |
   | - Manifest V3 Sidecar     |                 | - HMAC Audit Receipts     |
   | - MutationObserver & DOM  |                 +---------------------------+
   +---------------------------+
```

---

## 🛠️ Components

1. **`utils.py`**:
   - RFC 9562 compliant UUIDv7 generator.
   - Regex-based PII Redactor for Social Security Numbers, Credit Cards, and API Tokens.
   - HMAC-SHA256 cryptographic signature generator and constant-time verifier.

2. **`agenttrace_sdk.py` (Python SDK)**:
   - `AgentTraceTracker` for non-blocking background queue streaming.
   - `trace_session(task_name)` context manager bound to execution scope.
   - Wrappers for OpenAI / LLM completions capturing prompt tokens, completion strings, tool calls, and state variables.

3. **`gateway.py` (FastAPI Proxy Gateway)**:
   - Sub-10ms reverse proxy intercepting `POST /v1/chat/completions`.
   - Automatic `X-AgentTrace-Correlation-ID` header propagation.
   - Real-time PII redaction and HMAC-SHA256 signature payload generation.

4. **`extension/` (Chrome Auditor Extension)**:
   - Manifest V3 compliant extension with `content.js` and background service worker `background.js`.
   - `MutationObserver` capturing structural DOM deltas, click events, key presses, and input changes tagged with the active correlation ID.

5. **`ingest.py` (WORM Storage Vault)**:
   - Central ingestion endpoints (`/ingest/sdk`, `/ingest/gateway`, `/ingest/extension`).
   - Session joining by Correlation ID.
   - Write-Once-Read-Many (WORM) sealing endpoint (`POST /ingest/seal`) generating `proof.json`.

---

## ⚡ Quickstart & Testing

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run End-to-End Cryptographic Audit Verification

Run the self-healing test suite to spin up the servers, execute an SDK trace session, proxy a request through the Gateway, ingest Chrome extension DOM deltas, and verify `proof.json`:

```bash
python test_agenttrace.py
```

### 3. Run Performance Benchmark Suite

Execute the benchmark suite to measure latency overhead, PII redaction throughput, and generate competitive comparison matrices:

```bash
python benchmark.py
```

---

## 📊 Benchmark Metrics & Competitor Comparison

| Architectural Metric | **AgentTrace MVP** | **LangSmith** | **Helicone** | **Arize Phoenix** |
| :--- | :--- | :--- | :--- | :--- |
| **Proxy Added Latency (p50)** | **1.63 ms** *(Sub-10ms Target)* | N/A *(SDK Cloud Hook)* | 15.0 - 35.0 ms | N/A *(OTel Collector)* |
| **SDK Main Thread Overhead** | **0.0039 ms** *(3.9 µs Async Queue)* | 1.5 - 5.0 ms | N/A *(Proxy)* | 0.8 - 2.5 ms |
| **PII Redaction Engine** | **Inline Regex** *(84.7k ops/s)* | Post-hoc Cloud | Optional Proxy Rules | None *(Raw Ingestion)* |
| **Cryptographic Proofs** | **HMAC-SHA256 WORM Receipts** | None *(DB Records)* | None *(DB Logs)* | None |
| **DOM Mutation Sidecar** | **Manifest V3 Sidecar** | None | None | None |
| **Unified Correlation ID** | **RFC 9562 UUIDv7** | Custom Session ID | Header Request ID | Trace ID (UUIDv4) |

Full empirical benchmark metrics are exported to **[benchmark_results.json](file:///c:/Users/codew/agentrace/benchmark_results.json)**.

---

## 🔐 Cryptographic Proof Manifest (`proof.json`)

When an audit session is sealed via `POST /ingest/seal`, an immutable receipt is written:

```json
{
  "correlation_id": "019fc3d3-232a-78a4-ae9b-78322fadc2bf",
  "timestamp": 1785696829.1918862,
  "hmac_signature": "1c9de70ac5083c9ee1d5178deffd52eec78259c7c0589267997284c95b5b010d",
  "sdk_event_count": 1,
  "gateway_event_count": 1,
  "extension_event_count": 1,
  "integrity_status": "VERIFIED_WORM_IMMUTABLE"
}
```

---

## 📜 License

MIT License. Developed for enterprise multi-agent compliance auditing.