"""
LLMWitness Community - Concurrent Request Smoke Test
Checks a small, bounded batch of concurrent requests against local test services.
"""

import concurrent.futures
import os
import socket
import subprocess
import sys
import time

import httpx
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llmwitness.utils import generate_uuidv7


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def gateway_server():
    ingest_port = find_free_port()
    gateway_port = find_free_port()

    ingest_url = f"http://127.0.0.1:{ingest_port}"
    gateway_url = f"http://127.0.0.1:{gateway_port}"

    env = os.environ.copy()
    env["LLMWITNESS_MOCK_UPSTREAM"] = "true"
    env["INGESTION_SERVER_URL"] = ingest_url

    p1 = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "llmwitness.ingest:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(ingest_port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    p2 = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "llmwitness.gateway:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(gateway_port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )

    client = httpx.Client(timeout=1.0)
    for _ in range(30):
        try:
            if client.get(f"{gateway_url}/docs").status_code == 200:
                break
        except Exception:
            time.sleep(0.2)
    client.close()

    yield gateway_url

    for p in (p1, p2):
        p.terminate()
        try:
            p.wait(timeout=2.0)
        except Exception:
            p.kill()


def test_concurrent_gateway_load(gateway_server):
    workers = 20
    requests_per_worker = 10
    total_requests = workers * requests_per_worker
    errors = 0
    latencies = []

    def worker_job():
        nonlocal errors
        client = httpx.Client(timeout=10.0)
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Load test query string"}],
        }
        for _ in range(requests_per_worker):
            cid = generate_uuidv7()
            t0 = time.perf_counter()
            try:
                res = client.post(
                    f"{gateway_server}/v1/chat/completions",
                    json=payload,
                    headers={"X-LLMWitness-Correlation-ID": cid},
                )
                t1 = time.perf_counter()
                if res.status_code == 200:
                    latencies.append((t1 - t0) * 1000)
                else:
                    errors += 1
            except Exception:
                errors += 1
        client.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker_job) for _ in range(workers)]
        concurrent.futures.wait(futures)

    assert errors == 0, f"Encountered {errors} request errors during load test"
    assert len(latencies) == total_requests
