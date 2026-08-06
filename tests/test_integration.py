"""
AgentTrace Production Testing - Integration Test Suite
Verifies end-to-end telemetry flow: Python SDK -> Gateway Proxy -> Ingestion Server -> WORM Audit Seal.
"""

import json
import os
import socket
import subprocess
import sys
import time
import httpx
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agenttrace_sdk import AgentTraceTracker
from utils import generate_uuidv7, verify_proof_receipt


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def servers():
    ingest_port = find_free_port()
    gateway_port = find_free_port()

    ingest_url = f"http://127.0.0.1:{ingest_port}"
    gateway_url = f"http://127.0.0.1:{gateway_port}"

    env = os.environ.copy()
    env["AGENTTRACE_MOCK_UPSTREAM"] = "true"
    env["INGESTION_SERVER_URL"] = ingest_url

    ingest_cmd = [sys.executable, "-m", "uvicorn", "ingest:app", "--host", "127.0.0.1", "--port", str(ingest_port)]
    gateway_cmd = [sys.executable, "-m", "uvicorn", "gateway:app", "--host", "127.0.0.1", "--port", str(gateway_port)]

    ingest_proc = subprocess.Popen(ingest_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    gateway_proc = subprocess.Popen(gateway_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

    client = httpx.Client(timeout=1.0)
    for _ in range(30):
        try:
            r1 = client.get(f"{ingest_url}/docs")
            r2 = client.get(f"{gateway_url}/docs")
            if r1.status_code == 200 and r2.status_code == 200:
                break
        except Exception:
            time.sleep(0.2)
    client.close()

    yield {"ingest_url": ingest_url, "gateway_url": gateway_url}

    for p in (ingest_proc, gateway_proc):
        p.terminate()
        try:
            p.wait(timeout=2.0)
        except Exception:
            p.kill()


def test_full_integration_pipeline_and_worm_sealing(servers):
    ingest_url = servers["ingest_url"]
    gateway_url = servers["gateway_url"]

    tracker = AgentTraceTracker(ingestion_url=ingest_url)
    correlation_id = generate_uuidv7()

    with tracker.trace_session(task_name="integration_task", correlation_id=correlation_id):
        tracker.record_event(
            prompt_tokens=50,
            completion_tokens=100,
            completion_string="Integration response string",
            tool_calls=[{"name": "test_tool", "arguments": {"param": 1}}]
        )

    tracker.flush()
    tracker.shutdown()

    # Call Gateway through proxy
    client = httpx.Client(timeout=5.0)
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "Verify SSN 123-45-6789"}]
    }
    headers = {
        "X-AgentTrace-Correlation-ID": correlation_id,
        "X-AgentTrace-Enable-Caching": "true"
    }

    res = client.post(f"{gateway_url}/v1/chat/completions", json=payload, headers=headers)
    assert res.status_code == 200

    time.sleep(0.5)

    # Verify PII redaction in Ingestion Vault
    session_res = client.get(f"{ingest_url}/ingest/session/{correlation_id}")
    assert session_res.status_code == 200
    session_data = session_res.json()
    assert len(session_data["gateway_events"]) >= 1
    assert "[REDACTED_SSN]" in json.dumps(session_data["gateway_events"][0]["redacted_request"])

    # Seal WORM proof session
    seal_res = client.post(f"{ingest_url}/ingest/seal", json={"correlation_id": correlation_id})
    assert seal_res.status_code == 200
    seal_json = seal_res.json()
    assert seal_json["status"] == "sealed"
    assert "hmac_signature" in seal_json

    client.close()
