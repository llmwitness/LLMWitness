# Changelog

All notable changes to the AgentTrace project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-07

### Added
- **Python Telemetry SDK**: Asynchronous `AgentTraceTracker` daemon worker pushing telemetry events to internal `queue.Queue` with sub-microsecond main-thread overhead.
- **FastAPI Gateway Proxy**: High-concurrency reverse proxy (`gateway.py`) supporting OpenAI `/v1/chat/completions` API format and mock upstream execution mode (`AGENTTRACE_MOCK_UPSTREAM=true`).
- **Deep-JSON & Multi-Modal PII Redaction Engine**: Out-of-band PII scrubbing for SSNs, Credit Cards, API Tokens (`sk-...`), and Base64 vision payload images (`data:image/...`).
- **State-Aware Semantic Cache**: Header-driven (`X-AgentTrace-Enable-Caching: true`) caching engine returning instant cache hits for matching state hashes (`X-AgentTrace-State-Hash`).
- **WORM Cryptographic Proof Vault**: Deterministic HMAC-SHA256 audit log manifest sealing with Ed25519 asymmetric digital signatures and standalone verification via `verify_proof_receipt()`.
- **Chrome Extension Manifest V3 Sidecar**: DOM MutationObserver content script (`content.js`) tracking user-agent interactions.
- **Unified RFC 9562 UUIDv7**: Microsecond timestamped UUIDv7 correlation IDs linking SDK sessions, Gateway proxy requests, and browser sidecar logs.
- **Benchmark Suite**: Complete 14-target benchmark suite (`benchmarks/run_benchmarks.py`) with hardware metadata capture, warm-up/measurement phases, and CSV/JSON/Markdown exports.
- **Production Testing Suite**: Integration, load, fuzzing, hypothesis property, chaos, browser compatibility, docker, performance SLA, and security regression tests in `tests/`.
- **Packaging Support**: Standard PEP 517 / PEP 621 packaging (`pyproject.toml`, `setup.py`, `MANIFEST.in`, `PACKAGING.md`).
