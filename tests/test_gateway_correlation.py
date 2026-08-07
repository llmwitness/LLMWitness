import asyncio
import json
import os
import sys
import uuid

import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import llmwitness.gateway as gateway
from llmwitness.utils import generate_uuidv7, redact_payload


def request(app, method, path, **kwargs):
    async def run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(run())


def test_gateway_generates_uuidv7_when_header_is_absent(monkeypatch):
    monkeypatch.setenv("LLMWITNESS_MOCK_UPSTREAM", "true")
    response = request(
        gateway.app,
        "POST",
        "/v1/chat/completions",
        json={"model": "test", "messages": []},
    )

    correlation_id = response.headers["X-LLMWitness-Correlation-ID"]
    parsed = uuid.UUID(correlation_id)
    assert parsed.version == 7
    assert parsed.variant == uuid.RFC_4122


def test_gateway_preserves_valid_uuidv7_and_rejects_other_ids(monkeypatch):
    monkeypatch.setenv("LLMWITNESS_MOCK_UPSTREAM", "true")
    correlation_id = generate_uuidv7()
    response = request(
        gateway.app,
        "POST",
        "/v1/chat/completions",
        headers={"X-LLMWitness-Correlation-ID": correlation_id},
        json={"model": "test", "messages": []},
    )
    assert response.headers["X-LLMWitness-Correlation-ID"] == correlation_id

    invalid = request(
        gateway.app,
        "POST",
        "/v1/chat/completions",
        headers={"X-LLMWitness-Correlation-ID": "not-a-uuid"},
        json={"model": "test", "messages": []},
    )
    assert invalid.status_code == 400


def test_gateway_forwards_correlation_id_upstream(monkeypatch):
    monkeypatch.setenv("LLMWITNESS_MOCK_UPSTREAM", "false")
    correlation_id = generate_uuidv7()
    seen = {}

    async def handler(request):
        if request.url.path == "/v1/chat/completions":
            seen["correlation_id"] = request.headers.get("X-LLMWitness-Correlation-ID")
        return httpx.Response(200, json={"choices": []})

    old_client = gateway.http_client
    gateway.http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        response = request(
            gateway.app,
            "POST",
            "/v1/chat/completions",
            headers={"X-LLMWitness-Correlation-ID": correlation_id},
            json={"model": "test", "messages": []},
        )
    finally:
        asyncio.run(gateway.http_client.aclose())
        gateway.http_client = old_client

    assert response.status_code == 200
    assert seen["correlation_id"] == correlation_id
    assert response.headers["X-LLMWitness-Correlation-ID"] == correlation_id


def test_deep_redaction_masks_nested_patterns_and_sensitive_fields():
    payload = {
        "messages": [
            {
                "content": json.dumps(
                    {"profile": {"ssn": "123-45-6789", "password": "short-secret"}}
                )
            }
        ],
        "metadata": {"authorization": "Basic abc", "api_key": "tiny"},
    }
    redacted = redact_payload(payload)
    serialized = json.dumps(redacted)

    assert "123-45-6789" not in serialized
    assert "short-secret" not in serialized
    assert "Basic abc" not in serialized
    assert "tiny" not in serialized
    assert "[REDACTED_SSN]" in serialized
    assert serialized.count("[REDACTED_SENSITIVE_FIELD]") == 3
