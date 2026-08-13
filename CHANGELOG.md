# Changelog

## Unreleased

- Redacted tuple, set, and frozenset values that previously reached telemetry unscrubbed.
- Rejected non-finite JSON number literals with 422 instead of failing while rendering the validation error.
- Stopped allow-list placeholder tokens supplied in model output from being rewritten into allow-listed terms.
- Stopped an inline `data:image` payload from swallowing the text that follows it.
- Mapped receipt-directory creation failures to 507 alongside the existing write failures.
- Added edge-case suites for redaction, key handling, the SDK queue and lifecycle, both services, and the CLI.

## 0.1.0 — 2026-08-07

- Renamed the project and import namespace to LLMWitness.
- Defined Community as a single-user localhost toolkit with explicit limitations.
- Added canonical Ed25519 receipt signing and self-contained verification.
- Added per-session receipt files and fail-closed persistence errors.
- Added UUIDv7 validation, event/session bounds, and storage-boundary scrubbing.
- Removed the unsafe shared semantic cache and response-mutating audit behavior.
- Added a packaged `llmwitness` CLI.
- Removed duplicate compatibility modules, stale generated benchmark results, and unsupported deployment material.
- Replaced unsupported privacy, immutability, performance, compliance, and production claims with explicit limitations.
