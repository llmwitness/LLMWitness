# Community architecture

```text
Python SDK ───────────────┐
Browser component ───────┼─> local ingestion memory ─> per-session signed receipt file
Local JSON gateway ──────┘
        │
        └─> upstream chat-completions endpoint
```

Every path accepts the same UUIDv7 correlation identifier so callers can correlate events across components. Components generate independent identifiers when the caller does not propagate one. The gateway scrubs only the telemetry copy and returns the upstream response body to the caller unchanged. Ingestion scrubs received events again because caller-supplied fields are not trusted.

The default services are single-process and in-memory. Receipt files are tamper-evident local artifacts, not durable immutable storage. Authentication, tenancy, distributed coordination, retention enforcement, streaming, and high availability are outside the Community boundary.
