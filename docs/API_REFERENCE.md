# AgentTrace REST API Reference

This document provides complete specification for all HTTP endpoints exposed by the Ingestion Service (`ingest.py`) and Gateway Proxy (`gateway.py`).

---

## 1. Gateway Proxy Endpoints (`gateway.py`)

### `POST /v1/chat/completions`

Proxies LLM chat completion requests to upstream models with out-of-band PII redaction and state-aware semantic caching.

#### Request Headers:
- `X-AgentTrace-Correlation-ID` *(string, optional)*: RFC 9562 UUIDv7 correlation ID linking session events.
- `X-AgentTrace-Enable-Caching` *(string, optional)*: Set to `"true"` to enable state-aware semantic cache.
- `X-AgentTrace-State-Hash` *(string, optional)*: Unique hash representing current agent memory/state.
- `X-AgentTrace-Disable-PII-Scrubbing` *(string, optional)*: Set to `"true"` to bypass PII redaction (e.g. testing).

#### Request Body:
```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": "Verify SSN 123-45-6789"
    }
  ]
}
```

#### Response Headers:
- `X-AgentTrace-Cache-Hit`: `"true"` or `"false"`
- `X-AgentTrace-Cost-Saved`: `"100%"` (if cache hit)

---

## 2. Ingestion Service Endpoints (`ingest.py`)

### `POST /ingest/event`
Receives asynchronous telemetry event payloads from Python SDK or Browser Extension sidecars.

#### Request Body:
```json
{
  "correlation_id": "019fd8c2-0826-73ec-bee4-3591b25b6574",
  "source": "sdk",
  "event_type": "telemetry",
  "payload": {
    "task_name": "autonomous_financial_task",
    "prompt_tokens": 42,
    "completion_tokens": 108
  }
}
```

### `POST /ingest/seal`
Seals an audit session and computes WORM HMAC-SHA256 digests and Ed25519 digital proof receipts.

#### Request Body:
```json
{
  "correlation_id": "019fd8c2-0826-73ec-bee4-3591b25b6574"
}
```

#### Response Body:
```json
{
  "status": "sealed",
  "correlation_id": "019fd8c2-0826-73ec-bee4-3591b25b6574",
  "hmac_signature": "a1b2c3d4...",
  "ed25519_signature": "Base64SignatureString...",
  "public_key_fingerprint": "sha256_fingerprint_hex..."
}
```

### `GET /health`
Returns service readiness status.
