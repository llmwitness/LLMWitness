"""
Legacy compatibility layer for gateway.
Forwards FastAPI application and helper handlers to agenttrace.gateway.
"""

from agenttrace.gateway import (
    INGESTION_SERVER_URL,
    UPSTREAM_OPENAI_URL,
    app,
    chat_completions_proxy,
    deduplicate_system_prompts,
    hash_prompt_messages,
    http_client,
    key_manager,
    semantic_cache,
    send_gateway_telemetry,
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8011)
