# AgentTrace Migration & Upgrade Guide

This guide details how to integrate AgentTrace into existing LLM applications and upgrade legacy telemetry implementations.

---

## Migrating Direct OpenAI / Anthropic API Calls to AgentTrace Gateway

### Before Migration (Direct API Call):
```python
import openai

client = openai.OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Analyze user report"}]
)
```

### After Migration (Via AgentTrace Gateway Proxy):
```python
import openai

# Point base_url to AgentTrace Gateway Proxy
client = openai.OpenAI(
    api_key="sk-...",
    base_url="http://localhost:8011/v1"
)

# Optional compliance headers passed via default_headers
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Analyze user report"}],
    extra_headers={
        "X-AgentTrace-Enable-Caching": "true",
        "X-AgentTrace-State-Hash": "session_state_v1"
    }
)
```

---

## Upgrading Telemetry to Unified UUIDv7 Session Tracing

To ensure full cross-layer traceability between Python SDK telemetry, Gateway LLM proxy requests, and Chrome Extension browser sidecars:

1. Generate a single RFC 9562 UUIDv7 correlation ID per session:
   ```python
   from utils import generate_uuidv7
   correlation_id = generate_uuidv7()
   ```
2. Pass `correlation_id` to both the SDK trace context and Gateway request headers:
   ```python
   with tracker.trace_session(task_name="my_task", correlation_id=correlation_id):
       # Agent logic...
       pass
   ```
