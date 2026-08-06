# AgentTrace Technical Architecture Specification

This document details the system design, data flow, component breakdown, and state model of AgentTrace.

---

## 1. High-Level Architecture Overview

AgentTrace provides an immutable audit logging pipeline and edge compliance proxy designed for multi-agent autonomous AI workflows. It decouples high-frequency telemetry collection from LLM inference through asynchronous queuing, out-of-band PII sanitization, and asymmetric digital signatures.

```mermaid
graph TD
    subgraph Agent Runtime Layer
        SDK["Python SDK (AgentTraceTracker)"]
        Browser["Chrome Extension Sidecar / JS SDK"]
    end

    subgraph Edge Proxy Layer (gateway.py)
        Proxy["FastAPI Reverse Proxy (/v1/chat/completions)"]
        PII["Deep-JSON & Multi-Modal PII Engine"]
        Cache["State-Aware Semantic Cache"]
    end

    subgraph Immutable Vault Layer (ingest.py)
        IngestService["Ingestion Microservice (/ingest/event)"]
        Vault["WORM Audit Vault (proof.json)"]
        Crypto["Ed25519 Asymmetric Signer"]
    end

    SDK -->|Async Queue Worker| IngestService
    Browser -->|DOM Mutations| IngestService
    SDK -->|LLM Requests| Proxy
    Proxy --> PII
    PII --> Cache
    Cache -->|Proxy Stream| UpstreamLLM["Upstream LLM Provider"]
    Proxy -->|Correlation ID Audit Record| IngestService
    IngestService --> Vault
    Vault --> Crypto
```

---

## 2. Core Component Design

### 2.1 Python Telemetry SDK (`agenttrace_sdk.py`)
- **Non-Blocking Architecture**: Uses an internal `queue.Queue` coupled to a daemon worker thread (`AgentTraceTelemetryWorker`).
- **Context Manager**: `with tracker.trace_session(...) as cid:` automatically generates an RFC 9562 UUIDv7 correlation ID.
- **Fail-Safe Enqueueing**: Main thread calls to `record_event()` complete in microsecond latencies without blocking agent execution.

### 2.2 Edge Gateway Proxy (`gateway.py`)
- **OpenAI API Compatibility**: Exposes `/v1/chat/completions` accepting standard OpenAI/Anthropic request shapes.
- **PII Scrubbing**: Sanitizes sensitive fields in requests and responses out-of-band prior to log storage.
- **State-Aware Semantic Caching**: Identical prompts evaluated with matching state hashes (`X-AgentTrace-State-Hash`) return cached responses immediately.

### 2.3 Cryptographic WORM Vault (`ingest.py` & `utils.py`)
- **Unified Correlation**: Cross-links SDK trace logs, Gateway proxy calls, and browser extension events using a single UUIDv7 ID.
- **Session Sealing**: When an audit session is completed (`POST /ingest/seal`), AgentTrace computes an HMAC-SHA256 digest over deterministic JSON manifests and signs the result using Ed25519 key pairs.

### 2.4 Browser Sidecar (`agenttrace.js` & `extension/content.js`)
- **DOM Mutation Tracking**: Uses `MutationObserver` to record user interactions on AI web interfaces and pushes event payloads to the Ingestion service.
