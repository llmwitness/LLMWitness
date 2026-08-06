# AgentTrace Product & Engineering Roadmap

This document outlines the multi-phase engineering roadmap for AgentTrace.

---

## Phase 1 — MVP & Open Source Release (v0.1.0) [CURRENT]

- [x] Python Telemetry SDK (`AgentTraceTracker`) with non-blocking queue worker.
- [x] FastAPI Gateway Proxy with OpenAI format chat completion forwarding.
- [x] Deep-JSON & Multi-Modal PII Redaction Engine (SSNs, CCs, Tokens, Base64 vision images).
- [x] State-Aware Semantic Caching (100% cost reduction on matching prompt + state hash).
- [x] Unified RFC 9562 UUIDv7 Correlation ID linking across SDK, Gateway, and Browser.
- [x] Cryptographic WORM Proof Vault with Ed25519 digital signatures and HMAC receipts.
- [x] Chrome Extension Manifest V3 MutationObserver sidecar (`content.js`).
- [x] Comprehensive Benchmark Suite & Production Testing Matrix.

---

## Phase 2 — Production Hardening & Cloud Integrations (v1.0.0)

- [ ] OpenTelemetry (OTel) OTLP Exporter integration for Jaeger / Datadog trace exports.
- [ ] Distributed Redis Caching Backend for multi-node Gateway deployments.
- [ ] Enterprise Multi-Tenant API Authentication & Key Management.
- [ ] Webhook Event Subscriptions for real-time compliance alerting.
- [ ] Dynamic Web Dashboard for session visualization and audit proof verification.

---

## Phase 3 — High-Performance Kernel & Cloud Scale (v2.0.0)

- [ ] eBPF Kernel Network Sidecar for zero-overhead packet level audit tracing.
- [ ] S3 Object Storage Object Lock integration for cloud native WORM compliance.
- [ ] Streaming Token-Level PII Scrubbing for real-time SSE LLM completion streams.
- [ ] Automated Policy Engine for agent action block rules and rate-limiting.
