# Local API reference

All examples are localhost-only. If `LLMWITNESS_INGEST_TOKEN` is configured, send `Authorization: Bearer <token>` to ingestion routes.

- `POST /ingest/sdk` — bounded SDK telemetry.
- `POST /ingest/gateway` — bounded gateway audit telemetry.
- `POST /ingest/extension` — bounded browser telemetry.
- `POST /ingest/seal` — create one receipt for an existing correlation ID.
- `GET /ingest/session/{correlation_id}` — inspect an in-memory local session.
- `GET /health` — process health.
- `POST /v1/chat/completions` — bounded JSON development proxy.

Correlation IDs must be RFC 9562 UUIDv7 values. Creating a receipt prevents additional events for that in-memory session. Receipt creation can fail if storage fails or the target file already exists.

These are `0.x` APIs and may evolve in later releases with documented release notes.
