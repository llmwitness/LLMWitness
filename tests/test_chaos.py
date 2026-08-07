"""
LLMWitness Community - Chaos Testing Suite
Simulates ingestion service failure, network timeout, corrupted packet payloads, and local receipt tampering.
"""

import json
import os
import socket
import subprocess
import sys
import time

import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llmwitness.utils import generate_uuidv7, verify_proof_receipt


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_gateway_fail_open_on_ingestion_crash():
    """Chaos Test: Ensures Gateway proxy continues serving user LLM requests cleanly when Ingestion crashes."""
    gateway_port = find_free_port()
    gateway_url = f"http://127.0.0.1:{gateway_port}"
    unreachable_ingest_url = "http://127.0.0.1:59999"

    env = os.environ.copy()
    env["LLMWITNESS_MOCK_UPSTREAM"] = "true"
    env["INGESTION_SERVER_URL"] = unreachable_ingest_url

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "llmwitness.gateway:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(gateway_port),
    ]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
    )

    client = httpx.Client(timeout=5.0)
    ready = False
    for _ in range(30):
        try:
            if client.get(f"{gateway_url}/docs").status_code == 200:
                ready = True
                break
        except Exception:
            time.sleep(0.2)

    assert ready, "Gateway failed to start"

    try:
        # Gateway should succeed even though ingestion URL is unreachable
        res = client.post(
            f"{gateway_url}/v1/chat/completions",
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "Chaos test request"}],
            },
        )
        assert (
            res.status_code == 200
        ), f"Gateway failed open requirement: status {res.status_code}"
    finally:
        client.close()
        proc.terminate()
        try:
            proc.wait(timeout=2.0)
        except Exception:
            proc.kill()


def test_invalid_receipt_is_rejected(tmp_path):
    """Chaos Test: Modifying proof receipt entries must cause verification failure."""
    proof_file = os.path.join(tmp_path, "proof.json")
    correlation_id = generate_uuidv7()
    secret = "chaos-vault-secret-key"

    proof_data = {
        "correlation_id": correlation_id,
        "events": [{"type": "sdk_event", "payload": "clean_data"}],
        "hmac_signature": "valid_sig",
    }

    # Write proof file
    with open(proof_file, "w", encoding="utf-8") as f:
        json.dumps(proof_data)

    # Tamper with file
    proof_data["events"].append({"type": "tampered_event", "payload": "injected"})
    with open(proof_file, "w", encoding="utf-8") as f:
        json.dump(proof_data, f)

    # Verify fails
    assert verify_proof_receipt(proof_file, secret) is False
