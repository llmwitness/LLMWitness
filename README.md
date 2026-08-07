# LLMWitness Community

LLMWitness Community is a **local-first telemetry toolkit for AI-agent runs**. It correlates SDK, gateway, and browser events with UUIDv7 identifiers, applies best-effort pattern scrubbing to audit copies, and creates locally verifiable tamper-evident receipts.

> **Community limitations:** `0.1.0` is intended for single-user localhost development. Pattern scrubbing cannot guarantee removal of all personal or secret data. Local receipt files are ordinary files—not immutable storage, WORM storage, legal evidence, or a compliance certification. Telemetry delivery is best-effort. Do not expose the services to untrusted networks or use them as a high-security production control plane.

## Available now

- Python SDK with a bounded background telemetry queue and observable drop/failure counters.
- RFC 9562 UUIDv7 execution correlation.
- Localhost OpenAI chat-completions JSON proxy.
- Best-effort SSN, payment-card, token, sensitive-field, and image-payload pattern scrubbing for audit copies.
- Local Ed25519-signed receipts with optional HMAC verification.
- Browser SDK and opt-in Manifest V3 extension.
- `llmwitness verify` and `llmwitness validate-config` commands.

The gateway returns the upstream response body to the application without applying audit redaction to that response. Streaming, broad OpenAI compatibility, Anthropic compatibility, multi-tenancy, durable delivery, and distributed operation are not currently claimed.

## Install from source

No PyPI release is claimed by this repository yet.

```bash
git clone https://github.com/llmwitness/LLMWitness.git
cd LLMWitness
python -m pip install -e ".[dev]"
```

Start the local services in separate terminals:

```bash
python -m uvicorn llmwitness.ingest:app --host 127.0.0.1 --port 8000
python -m uvicorn llmwitness.gateway:app --host 127.0.0.1 --port 8011
```

## Python SDK

```python
from llmwitness import LLMWitnessTracker

tracker = LLMWitnessTracker(ingestion_url="http://127.0.0.1:8000")
with tracker.trace_session("example") as correlation_id:
    tracker.record_event(
        completion_string="Example output",
        agent_state={"step": 1},
    )

tracker.flush()
tracker.shutdown()
print(correlation_id, tracker.dropped_events, tracker.delivery_failures)
```

If `LLMWITNESS_INGEST_TOKEN` is configured on the ingestion service, the SDK and gateway read the same variable and authenticate their telemetry submissions. Without a token, ingestion is restricted to loopback development clients.

## Create and verify a receipt

After telemetry exists for a correlation ID:

```bash
curl -X POST http://127.0.0.1:8000/ingest/seal \
  -H "Content-Type: application/json" \
  -d '{"correlation_id":"YOUR_UUIDV7"}'

llmwitness verify .llmwitness/receipts/YOUR_UUIDV7.json
```

Verification proves that the signed fields match the public key embedded in the receipt. It does **not** prove who controlled that key. Compare the displayed fingerprint with a trusted value when signer identity matters. Configure persistent key material before expecting verification across restarts; automatically generated keys are development-only.

## Product boundary

**LLMWitness Community — available in this Apache-2.0 repository:** the SDK, localhost gateway, heuristic scrubber, local ingestion service, local tamper-evident receipts, browser components, and CLI.

**LLMWitness Cloud — planned, not available:** a managed service, team dashboard, hosted analytics, and operational management. Its implementation is not in this repository and is intended to remain proprietary.

**LLMWitness Enterprise — planned, not available:** multi-tenancy, RBAC/SSO, distributed storage and cache, Object Lock, HSM/KMS, policy enforcement, high availability, reporting workflows, and enterprise UI. These components are not implemented here and are intended to remain proprietary.

LLMWitness does not establish compliance with HIPAA, GDPR, SOC 2, the EU AI Act, or any other law or framework. Applicability depends on the deployment, processing purposes, jurisdiction, contracts, technical controls, and organizational practices. Obtain qualified legal and security advice.

## Security model

Read [SECURITY.md](SECURITY.md) before using the project. The Community edition is not an authentication, authorization, replay-prevention, DLP, retention, or compliance system. UUIDv7 provides correlation and approximate creation ordering; it is not a security token.

## Benchmarks

No performance benchmark numbers are claimed or published for this release. The test suite checks correctness and bounded behavior; it is not evidence of production latency, throughput, scalability, or a service-level objective. Any future benchmark publication must include the exact commit, environment, workload, sample count, methodology, and raw results.

## License

LLMWitness Community is licensed under [Apache License 2.0](LICENSE). That license permits copying, modification, redistribution, and commercial use subject to its terms. Public code cannot be made physically impossible to copy; proprietary Cloud and Enterprise implementations must remain in separate private repositories.
