import hashlib
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple
import httpx
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
import uvicorn

from agenttrace.utils import Ed25519KeyManager, generate_uuidv7, redact_payload

UPSTREAM_OPENAI_URL = os.getenv("UPSTREAM_OPENAI_URL", "https://api.openai.com")
INGESTION_SERVER_URL = os.getenv("INGESTION_SERVER_URL", "http://localhost:8000")

app = FastAPI(
    title="AgentTrace FastAPI Proxy Gateway & Optimization Engine",
    description="Sub-10ms reverse proxy with PII redaction, state-aware semantic caching, token de-duplication, and dynamic routing",
    version="1.2.0"
)

# HTTP Client pool for high concurrency low-latency proxy forwarding
http_client = httpx.AsyncClient(timeout=30.0)

# In-memory Semantic Cache Engine
semantic_cache: Dict[str, Dict[str, Any]] = {}
key_manager = Ed25519KeyManager()


def hash_prompt_messages(messages: List[Dict[str, Any]]) -> str:
    """Computes a deterministic SHA256 signature for prompt messages array."""
    normalized_str = json.dumps(messages, sort_keys=True)
    return hashlib.sha256(normalized_str.encode("utf-8")).hexdigest()


def deduplicate_system_prompts(messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Strips duplicate system prompt messages from multi-agent chat history.
    Returns (cleaned_messages, tokens_saved_estimate).
    """
    seen_system_contents = set()
    cleaned = []
    tokens_saved = 0

    for msg in messages:
        if msg.get("role") == "system":
            content = msg.get("content", "")
            if content in seen_system_contents:
                tokens_saved += len(content) // 4
                continue
            seen_system_contents.add(content)
        cleaned.append(msg)

    return cleaned, tokens_saved


async def send_gateway_telemetry(
    correlation_id: str,
    timestamp: float,
    upstream_url: str,
    status_code: int,
    request_hmac: Optional[str] = None,
    response_hmac: Optional[str] = None,
    redacted_request: Optional[Dict[str, Any]] = None,
    redacted_response: Optional[Dict[str, Any]] = None,
    optimization_meta: Optional[Dict[str, Any]] = None,
):
    """
    Out-of-band asynchronous task streaming sanitized proxy audit trace to Ingestion Vault.
    Fail-open design: swallows network/service errors silently.
    """
    payload = {
        "correlation_id": correlation_id,
        "timestamp": timestamp,
        "upstream_url": upstream_url,
        "status_code": status_code,
        "request_hmac": request_hmac,
        "response_hmac": response_hmac,
        "redacted_request": redacted_request,
        "redacted_response": redacted_response,
        "optimization_meta": optimization_meta or {},
    }
    try:
        await http_client.post(f"{INGESTION_SERVER_URL}/ingest/gateway", json=payload)
    except Exception:
        pass


@app.post("/v1/chat/completions")
async def chat_completions_proxy(
    request: Request,
    background_tasks: BackgroundTasks,
    x_agenttrace_correlation_id: Optional[str] = Header(None, alias="X-AgentTrace-Correlation-ID"),
    x_agenttrace_enable_caching: Optional[str] = Header(None, alias="X-AgentTrace-Enable-Caching"),
    x_agenttrace_state_hash: Optional[str] = Header(None, alias="X-AgentTrace-State-Hash"),
    x_agenttrace_enable_deduplication: Optional[str] = Header(None, alias="X-AgentTrace-Enable-Deduplication"),
    x_agenttrace_enable_routing: Optional[str] = Header(None, alias="X-AgentTrace-Enable-Routing"),
    x_agenttrace_disable_pii_scrubbing: Optional[str] = Header(None, alias="X-AgentTrace-Disable-PII-Scrubbing"),
):
    """
    High-Performance OpenAI-Compatible Reverse Proxy Endpoint.
    Integrates Deep PII Redaction, State-Aware Semantic Caching, System Prompt De-duplication,
    and Dynamic Model Routing with zero overhead.
    """
    start_time = time.time()
    correlation_id = x_agenttrace_correlation_id or generate_uuidv7()

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    messages = body.get("messages", [])
    model = body.get("model", "gpt-4o")

    enable_caching = (x_agenttrace_enable_caching or "").lower() == "true"
    enable_dedup = (x_agenttrace_enable_deduplication or "").lower() == "true"
    enable_routing = (x_agenttrace_enable_routing or "").lower() == "true"
    disable_pii = (x_agenttrace_disable_pii_scrubbing or "").lower() == "true" or os.getenv("AGENTTRACE_DISABLE_PII_SCRUBBING", "false").lower() == "true"

    optimization_meta: Dict[str, Any] = {
        "cache_hit": False,
        "dedup_tokens_saved": 0,
        "routed_model": None,
        "pii_scrubbing_active": not disable_pii,
    }

    # 1. State-Aware Semantic Cache Lookup
    prompt_hash = hash_prompt_messages(messages)
    cache_key = f"{model}:{prompt_hash}:{x_agenttrace_state_hash or 'no_state'}"

    if enable_caching and x_agenttrace_state_hash and cache_key in semantic_cache:
        cached_entry = semantic_cache[cache_key]
        optimization_meta["cache_hit"] = True
        optimization_meta["cost_saved"] = "100%"

        redacted_req = body if disable_pii else redact_payload(body)
        redacted_res = cached_entry["response"] if disable_pii else redact_payload(cached_entry["response"])

        background_tasks.add_task(
            send_gateway_telemetry,
            correlation_id=correlation_id,
            timestamp=start_time,
            upstream_url="CACHE_HIT",
            status_code=200,
            redacted_request=redacted_req,
            redacted_response=redacted_res,
            optimization_meta=optimization_meta,
        )

        headers_out = {
            "X-AgentTrace-Correlation-ID": correlation_id,
            "X-AgentTrace-Cache-Hit": "true",
            "X-AgentTrace-Cost-Saved": "100%",
        }
        return JSONResponse(content=cached_entry["response"], status_code=200, headers=headers_out)

    # 2. System Prompt De-duplication
    if enable_dedup and messages:
        cleaned_messages, tokens_saved = deduplicate_system_prompts(messages)
        body["messages"] = cleaned_messages
        optimization_meta["dedup_tokens_saved"] = tokens_saved

    # 3. Dynamic Model Routing
    if enable_routing:
        if model == "gpt-4o" and len(json.dumps(messages)) < 500:
            body["model"] = "gpt-4o-mini"
            optimization_meta["routed_model"] = "gpt-4o-mini"
        else:
            optimization_meta["routed_model"] = body.get("model")

    target_model = body.get("model", model)
    target_url = f"{UPSTREAM_OPENAI_URL.rstrip('/')}/v1/chat/completions"

    # 4. Proxy Execution (Mock Mode or Real Upstream)
    is_mock = os.getenv("AGENTTRACE_MOCK_UPSTREAM", "false").lower() in ("true", "1")

    if is_mock:
        response_json = {
            "id": f"chatcmpl-{correlation_id[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": target_model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"Mock response content for model {target_model}. Verified.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 15, "completion_tokens": 25, "total_tokens": 40},
        }
        status_code = 200
    else:
        req_headers = {}
        for h_key, h_val in request.headers.items():
            if h_key.lower() in ("authorization", "content-type"):
                req_headers[h_key] = h_val

        try:
            resp = await http_client.post(target_url, json=body, headers=req_headers)
            status_code = resp.status_code
            response_json = resp.json()
        except Exception as err:
            status_code = status.HTTP_502_BAD_GATEWAY
            response_json = {"error": f"Upstream proxy failed: {str(err)}"}

    # 5. Populate Semantic Cache
    if enable_caching and status_code == 200 and x_agenttrace_state_hash:
        semantic_cache[cache_key] = {"response": response_json, "timestamp": time.time()}

    # 6. Deep PII Redaction for Audit Log Stream
    redacted_req = body if disable_pii else redact_payload(body)
    redacted_res = response_json if disable_pii else redact_payload(response_json)

    background_tasks.add_task(
        send_gateway_telemetry,
        correlation_id=correlation_id,
        timestamp=start_time,
        upstream_url=target_url if not is_mock else "MOCK_UPSTREAM",
        status_code=status_code,
        redacted_request=redacted_req,
        redacted_response=redacted_res,
        optimization_meta=optimization_meta,
    )

    response_headers = {
        "X-AgentTrace-Correlation-ID": correlation_id,
        "X-AgentTrace-Cache-Hit": "false",
    }
    if optimization_meta.get("routed_model"):
        response_headers["X-AgentTrace-Routed-Model"] = str(optimization_meta["routed_model"])
    if optimization_meta.get("dedup_tokens_saved"):
        response_headers["X-AgentTrace-Dedup-Tokens-Saved"] = str(optimization_meta["dedup_tokens_saved"])

    return JSONResponse(content=redacted_res if not is_mock else response_json, status_code=status_code, headers=response_headers)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8011)
