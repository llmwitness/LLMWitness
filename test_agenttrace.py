import json
import os
import subprocess
import sys
import time
import httpx

from agenttrace_sdk import AgentTraceTracker, trace_session
from utils import generate_uuidv7, verify_hmac_signature

SECRET_KEY = os.getenv("AGENTTRACE_SECRET_KEY", "agenttrace-production-worm-vault-key-2026")

import socket

def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

INGEST_PORT = find_free_port()
GATEWAY_PORT = find_free_port()

INGEST_URL = f"http://localhost:{INGEST_PORT}"
GATEWAY_URL = f"http://localhost:{GATEWAY_PORT}"
PROOF_FILE = "proof.json"

def start_server(module_name: str, port: int):
    """Launches a FastAPI uvicorn server in a separate background process."""
    cmd = [sys.executable, "-m", "uvicorn", f"{module_name}:app", "--host", "127.0.0.1", "--port", str(port)]
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


def run_e2e_test():
    print("==================================================================")
    print("   AGENTTRACE MVP END-TO-END CRYPTOGRAPHIC AUDIT TEST SUITE      ")
    print("==================================================================")
    
    # Clean old proof file
    if os.path.exists(PROOF_FILE):
        os.remove(PROOF_FILE)

    ingest_proc = None
    gateway_proc = None

    try:
        # Step 1: Start Ingestion Server & Gateway Server
        print("[1/6] Launching Ingestion Server (Port 8000) & Gateway (Port 8001)...")
        ingest_proc = start_server("ingest", INGEST_PORT)
        gateway_proc = start_server("gateway", GATEWAY_PORT)

        if not wait_for_server(INGEST_URL):
            raise RuntimeError("Ingestion Server failed to start on port 8000")
        if not wait_for_server(GATEWAY_URL):
            raise RuntimeError("Gateway Server failed to start on port 8001")
        print("      Ingestion Server & Gateway Proxy ready.")

        # Step 2: Initialize SDK Telemetry Session
        print("\n[2/6] Executing Python SDK trace session...")
        tracker = AgentTraceTracker(ingestion_url=INGEST_URL)
        
        with tracker.trace_session(task_name="autonomous_financial_agent_task") as cid:
            correlation_id = cid
            print(f"      Unified Correlation ID (UUIDv7): {correlation_id}")
            
            # Record SDK telemetry event
            tracker.record_event(
                prompt_tokens=42,
                completion_tokens=108,
                completion_string="Successfully performed compliance validation for transfer.",
                tool_calls=[{"name": "execute_wire_transfer", "arguments": {"amount": 5000}}],
                agent_state={"memory_step": 3, "risk_score": 0.02}
            )
            
        tracker.flush()
        print("      SDK telemetry recorded and queued asynchronously.")

        # Step 3: Send Request via Proxy Gateway with Sensitive PII
        print("\n[3/6] Sending chat completion request through Gateway Proxy...")
        client = httpx.Client(timeout=10.0)
        
        pii_request_payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": "Verify SSN 123-45-6789 and Card 4532-1111-2222-3333 with token sk-abcdef1234567890abcdef1234567890"
                }
            ]
        }
        
        headers = {
            "X-AgentTrace-Correlation-ID": correlation_id,
            "Authorization": "Bearer sk-testtoken12345678901234567890"
        }
        
        gateway_start = time.time()
        res = client.post(f"{GATEWAY_URL}/v1/chat/completions", json=pii_request_payload, headers=headers)
        gateway_latency_ms = (time.time() - gateway_start) * 1000
        
        assert res.status_code == 200, f"Gateway request failed with status {res.status_code}"
        assert res.headers.get("X-AgentTrace-Correlation-ID") == correlation_id, "Correlation ID mismatch in gateway response"
        print(f"      Gateway proxy request succeeded in {gateway_latency_ms:.2f} ms")

        # Step 4: Dispatch Chrome Extension Telemetry Payload
        print("\n[4/6] Simulating Chrome Auditor Extension DOM Mutation Telemetry...")
        extension_payload = {
            "correlation_id": correlation_id,
            "timestamp": time.time(),
            "url": "http://localhost:3000/agent/dashboard",
            "event_type": "dom_mutation",
            "element_id": "transfer-submit-btn",
            "dom_delta": {
                "type": "childList",
                "addedCount": 1,
                "addedNodesSummary": [{"nodeType": 1, "tagName": "DIV", "id": "status-alert"}]
            }
        }
        
        ext_res = client.post(f"{INGEST_URL}/ingest/extension", json=extension_payload)
        assert ext_res.status_code == 201, "Extension telemetry ingestion failed"
        print("      Extension telemetry ingested successfully.")

        # Give background tasks time to complete ingestion
        time.sleep(1.0)

        # Step 5: Verify Unified Ingestion Vault Payload
        print("\n[5/6] Verifying unified session audit trace in Ingestion Vault...")
        trace_res = client.get(f"{INGEST_URL}/ingest/session/{correlation_id}")
        assert trace_res.status_code == 200, "Session trace retrieval failed"
        session_data = trace_res.json()
        
        assert session_data["correlation_id"] == correlation_id, "Session correlation ID mismatch"
        assert len(session_data["sdk_events"]) >= 1, "Missing SDK events in unified trace"
        assert len(session_data["gateway_events"]) >= 1, "Missing Gateway events in unified trace"
        assert len(session_data["extension_events"]) >= 1, "Missing Extension events in unified trace"
        
        # Verify PII scrubbing in Gateway payload stored in Ingest
        gw_event = session_data["gateway_events"][0]
        redacted_req_str = json.dumps(gw_event["redacted_request"])
        assert "[REDACTED_SSN]" in redacted_req_str, "SSN PII redaction failed"
        assert "[REDACTED_CREDIT_CARD]" in redacted_req_str, "Credit Card PII redaction failed"
        assert "[REDACTED_API_TOKEN]" in redacted_req_str, "API Token PII redaction failed"
        print("      PII Redaction verified across Gateway payloads ([REDACTED_SSN], [REDACTED_CREDIT_CARD], [REDACTED_API_TOKEN]).")

        # Step 6: Seal Session & Output Cryptographic Proof Manifest
        print("\n[6/6] Sealing WORM Session and generating proof.json manifest...")
        seal_res = client.post(f"{INGEST_URL}/ingest/seal", json={"correlation_id": correlation_id})
        assert seal_res.status_code == 200, "Sealing session failed"
        seal_data = seal_res.json()
        
        print(f"      Session sealed. HMAC Signature: {seal_data['hmac_signature']}")
        assert os.path.exists(PROOF_FILE), "proof.json manifest was not created"
        
        with open(PROOF_FILE, "r", encoding="utf-8") as f:
            proofs = json.load(f)
            
        assert len(proofs) >= 1, "Empty proof manifest"
        latest_proof = proofs[-1]
        assert latest_proof["correlation_id"] == correlation_id, "Proof correlation ID mismatch"
        assert latest_proof["integrity_status"] == "VERIFIED_WORM_IMMUTABLE", "Proof integrity status invalid"
        
        print(f"      Cryptographic Proof Manifest saved to {os.path.abspath(PROOF_FILE)}")
        print("\n==================================================================")
        print("   SUCCESS! ALL AGENTTRACE E2E CRYPTOGRAPHIC AUDIT TESTS PASSED.   ")
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
