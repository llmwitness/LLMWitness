import base64
import json
import os
import socket
import subprocess
import sys
import time
import httpx

from agenttrace_sdk import AgentTraceTracker, trace_session
from utils import (
    Ed25519KeyManager,
    generate_uuidv7,
    redact_payload,
    verify_proof_receipt,
)

SECRET_KEY = os.getenv("AGENTTRACE_SECRET_KEY", "agenttrace-production-worm-vault-key-2026")


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


INGEST_PORT = find_free_port()
GATEWAY_PORT = find_free_port()

INGEST_URL = f"http://localhost:{INGEST_PORT}"
GATEWAY_URL = f"http://localhost:{GATEWAY_PORT}"
PROOF_FILE = "proof.json"


def start_server(module_name: str, port: int):
    """Launches a FastAPI uvicorn server in a separate background process."""
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        f"{module_name}:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    env = os.environ.copy()
    env["AGENTTRACE_MOCK_UPSTREAM"] = "true"
    env["INGESTION_SERVER_URL"] = f"http://localhost:{INGEST_PORT}"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    return proc


def wait_for_server(url: str, timeout: float = 10.0) -> bool:
    """Waits until a server becomes responsive to HTTP requests."""
    start = time.time()
    client = httpx.Client(timeout=1.0)
    while time.time() - start < timeout:
        try:
            res = client.get(f"{url}/docs")
            if res.status_code == 200:
                client.close()
                return True
        except Exception:
            time.sleep(0.3)
    client.close()
    return False


def test_deep_json_and_multimodal_pii_redaction():
    print("\n--- Testing Deep-JSON & Multi-Modal PII Redaction Engine ---")

    # 1. Deep JSON with nested JSON string containing SSN and API token
    nested_json_str = json.dumps({"secret_token": "sk-12345678901234567890abcdef", "ssn": "987-65-4321"})
    payload = {
        "user_id": 101,
        "metadata": nested_json_str,
        "credit_card": "4111-2222-3333-4444",
        "safe_code": "ALLOW_ME_123"
    }

    redacted = redact_payload(payload, allow_list=["ALLOW_ME_123"])

    assert "[REDACTED_CREDIT_CARD]" in str(redacted["credit_card"])
    assert "ALLOW_ME_123" in redacted["safe_code"]
    # The embedded JSON string must have been parsed, redacted, and re-dumped
    redacted_meta = json.loads(redacted["metadata"])
    assert redacted_meta["secret_token"] == "[REDACTED_API_TOKEN]"
    assert redacted_meta["ssn"] == "[REDACTED_SSN]"
    print("  [OK] Deep-JSON & JSON string recursive PII redaction verified.")

    # 2. Multi-Modal Vision Payload Base64 Image Detection
    tiny_png_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    image_payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this screenshot"},
                    {"type": "image_url", "image_url": {"url": tiny_png_b64}}
                ]
            }
        ]
    }
    redacted_img = redact_payload(image_payload)
    img_url_val = redacted_img["messages"][0]["content"][1]["image_url"]["url"]
    assert img_url_val.startswith("[REDACTED_IMAGE_PAYLOAD_SIZE_") and img_url_val.endswith("_BYTES]")
    print(f"  [OK] Multi-Modal Data URI Base64 image redacted to: {img_url_val}")

    # 3. Raw Base64 string (>1000 chars) representing PNG image bytes
    raw_png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 1500
    raw_b64_img = base64.b64encode(raw_png_bytes).decode("utf-8")
    assert len(raw_b64_img) > 1000

    redacted_raw = redact_payload({"raw_vision_data": raw_b64_img})
    raw_val = redacted_raw["raw_vision_data"]
    assert raw_val.startswith("[REDACTED_IMAGE_PAYLOAD_SIZE_") and raw_val.endswith("_BYTES]")
    print(f"  [OK] Raw Base64 image string (>1000 chars) redacted to: {raw_val}")


def run_e2e_test():
    print("==================================================================")
    print("   AGENTTRACE UPGRADED CRYPTOGRAPHIC AUDIT & GATEWAY TEST SUITE  ")
    print("==================================================================")

    # First run standalone component tests
    test_deep_json_and_multimodal_pii_redaction()

    # Clean old proof file
    if os.path.exists(PROOF_FILE):
        os.remove(PROOF_FILE)

    ingest_proc = None
    gateway_proc = None

    try:
        # Step 1: Start Ingestion Server & Gateway Server
        print("\n[1/7] Launching Ingestion Server & Gateway Proxy...")
        ingest_proc = start_server("ingest", INGEST_PORT)
        gateway_proc = start_server("gateway", GATEWAY_PORT)

        if not wait_for_server(INGEST_URL):
            raise RuntimeError(f"Ingestion Server failed to start on port {INGEST_PORT}")
        if not wait_for_server(GATEWAY_URL):
            raise RuntimeError(f"Gateway Server failed to start on port {GATEWAY_PORT}")
        print("      Ingestion Server & Gateway Proxy ready.")

        # Step 2: Initialize SDK Telemetry Session
        print("\n[2/7] Executing Python SDK trace session...")
        tracker = AgentTraceTracker(ingestion_url=INGEST_URL)

        with tracker.trace_session(task_name="autonomous_financial_agent_task") as cid:
            correlation_id = cid
            print(f"      Unified Correlation ID (UUIDv7): {correlation_id}")

            tracker.record_event(
                prompt_tokens=42,
                completion_tokens=108,
                completion_string="Successfully performed compliance validation for transfer.",
                tool_calls=[{"name": "execute_wire_transfer", "arguments": {"amount": 5000}}],
                agent_state={"memory_step": 3, "risk_score": 0.02},
            )

        tracker.flush()
        print("      SDK telemetry recorded and queued asynchronously.")

        # Step 3: Send Request via Proxy Gateway with State Hash & PII
        print("\n[3/7] Testing Gateway Proxy with State-Aware Semantic Caching & Deep PII...")
        client = httpx.Client(timeout=10.0)

        pii_request_payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": "Verify SSN 123-45-6789 with token sk-abcdef1234567890abcdef1234567890",
                }
            ],
        }

        # Request 3A: Initial request with State Hash A and caching enabled
        headers_state_a = {
            "X-AgentTrace-Correlation-ID": correlation_id,
            "X-AgentTrace-State-Hash": "state_hash_v1_alpha",
            "X-AgentTrace-Enable-Caching": "true",
            "Authorization": "Bearer sk-testtoken12345678901234567890",
        }

        res1 = client.post(f"{GATEWAY_URL}/v1/chat/completions", json=pii_request_payload, headers=headers_state_a)
        assert res1.status_code == 200, f"Gateway request 1 failed: {res1.status_code}"
        assert res1.headers.get("X-AgentTrace-Cache-Hit") == "false", "Expected cache miss on first request"

        # Request 3B: Identical prompt with SAME State Hash -> Cache HIT
        res2 = client.post(f"{GATEWAY_URL}/v1/chat/completions", json=pii_request_payload, headers=headers_state_a)
        assert res2.status_code == 200
        assert res2.headers.get("X-AgentTrace-Cache-Hit") == "true", "Expected cache hit on matching state hash"
        print("      [OK] Cache HIT confirmed for identical prompt + state hash.")

        # Request 3C: Identical prompt with CHANGED State Hash -> Cache MISS
        headers_state_b = {
            "X-AgentTrace-Correlation-ID": correlation_id,
            "X-AgentTrace-State-Hash": "state_hash_v2_beta",
            "X-AgentTrace-Enable-Caching": "true",
        }
        res3 = client.post(f"{GATEWAY_URL}/v1/chat/completions", json=pii_request_payload, headers=headers_state_b)
        assert res3.status_code == 200
        assert res3.headers.get("X-AgentTrace-Cache-Hit") == "false", "Expected cache miss on changed state hash"
        print("      [OK] Cache MISS confirmed on state hash change.")

        # Request 3D: Identical prompt WITHOUT State Hash -> Forced Cache MISS
        headers_no_state = {
            "X-AgentTrace-Correlation-ID": correlation_id,
            "X-AgentTrace-Enable-Caching": "true",
        }
        res4 = client.post(f"{GATEWAY_URL}/v1/chat/completions", json=pii_request_payload, headers=headers_no_state)
        assert res4.status_code == 200
        assert res4.headers.get("X-AgentTrace-Cache-Hit") == "false", "Expected forced cache miss when state hash header is missing"
        print("      [OK] Forced Cache MISS confirmed when X-AgentTrace-State-Hash is omitted.")

        # Step 4: Dispatch Headless JS Bridge Telemetry Event
        print("\n[4/7] Simulating Headless JS Bridge (agenttrace.js) Telemetry Ingestion...")
        headless_payload = {
            "correlation_id": correlation_id,
            "timestamp": time.time(),
            "url": "http://localhost:3000/agent/headless_nav",
            "event_type": "fetch_request",
            "element_id": "login-btn",
            "dom_delta": {"method": "POST", "url": "/api/action"},
        }

        ext_res = client.post(f"{INGEST_URL}/ingest/extension", json=headless_payload)
        assert ext_res.status_code == 201, "Headless JS Bridge telemetry ingestion failed"
        print("      Headless JS telemetry ingested successfully.")

        # Wait briefly for async background tasks
        time.sleep(1.0)

        # Step 5: Verify Unified Ingestion Vault Payload & Deep PII
        print("\n[5/7] Verifying unified session audit trace in Ingestion Vault...")
        trace_res = client.get(f"{INGEST_URL}/ingest/session/{correlation_id}")
        assert trace_res.status_code == 200, "Session trace retrieval failed"
        session_data = trace_res.json()

        assert session_data["correlation_id"] == correlation_id
        assert len(session_data["sdk_events"]) >= 1
        assert len(session_data["gateway_events"]) >= 1
        assert len(session_data["extension_events"]) >= 1

        gw_event = session_data["gateway_events"][0]
        redacted_req_str = json.dumps(gw_event["redacted_request"])
        assert "[REDACTED_SSN]" in redacted_req_str
        assert "[REDACTED_API_TOKEN]" in redacted_req_str
        print("      PII Redaction verified across Ingestion Vault payloads.")

        # Step 6: Seal Session & Output Ed25519 Proof Manifest
        print("\n[6/7] Sealing WORM Session with Ed25519 Digital Signature...")
        seal_res = client.post(f"{INGEST_URL}/ingest/seal", json={"correlation_id": correlation_id})
        assert seal_res.status_code == 200, "Sealing session failed"
        seal_data = seal_res.json()

        print(f"      Ed25519 Public Key Fingerprint: {seal_data['public_key_fingerprint']}")
        print(f"      ISO Timestamp (RFC 3339): {seal_data['timestamp_iso']}")
        print(f"      Ed25519 Signature (Base64): {seal_data['signature'][:32]}...")

        assert os.path.exists(PROOF_FILE), "proof.json manifest was not created"

        # Step 7: Verify Receipt with verify_proof_receipt helper
        print("\n[7/7] Verifying proof.json using standalone helper verify_proof_receipt()...")
        with open(PROOF_FILE, "r", encoding="utf-8") as f:
            proofs = json.load(f)

        latest_proof = proofs[-1]
        pub_key_pem = latest_proof["public_key_pem"]

        is_valid = verify_proof_receipt(PROOF_FILE, public_key_pem=pub_key_pem)
        assert is_valid, "verify_proof_receipt() failed to verify valid untampered Ed25519 receipt!"
        print("      [OK] verify_proof_receipt() successfully verified untampered Ed25519 WORM proof receipt.")

        # Test tamper detection by altering the manifest
        tampered_proof = dict(latest_proof)
        tampered_proof["proof_manifest"]["sealed_at"] += 999
        is_tampered_valid = verify_proof_receipt(tampered_proof, public_key_pem=pub_key_pem)
        assert not is_tampered_valid, "verify_proof_receipt() failed to detect tampered receipt!"
        print("      [OK] verify_proof_receipt() correctly rejected tampered receipt.")

        print("\n==================================================================")
        print("   SUCCESS! ALL AGENTTRACE ARCHITECTURAL FIX TESTS PASSED.         ")
        print("==================================================================")

        tracker.shutdown()
        client.close()

    finally:
        print("\nTerminating background server processes...")
        if gateway_proc:
            gateway_proc.terminate()
            gateway_proc.wait()
        if ingest_proc:
            ingest_proc.terminate()
            ingest_proc.wait()


if __name__ == "__main__":
    run_e2e_test()
