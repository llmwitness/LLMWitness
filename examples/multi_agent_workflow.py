"""
AgentTrace Multi-Agent Workflow Example
Demonstrates multi-agent telemetry tracking, state-hash cache optimization, and WORM session sealing.
"""

import os
import sys
import time
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agenttrace_sdk import AgentTraceTracker
from utils import generate_uuidv7, verify_proof_receipt


def run_multi_agent_workflow():
    print("==================================================================")
    print("   AGENTTRACE MULTI-AGENT WORKFLOW COMPLIANCE & PROOF DEMO       ")
    print("==================================================================")

    ingest_url = "http://localhost:8000"
    gateway_url = "http://localhost:8011"
    tracker = AgentTraceTracker(ingestion_url=ingest_url)
    correlation_id = generate_uuidv7()

    print(f"\n[1] Starting Multi-Agent Session | Correlation ID: {correlation_id}")

    # Agent A: Research Agent
    with tracker.trace_session(task_name="multi_agent_orchestration", correlation_id=correlation_id):
        print("  - Agent A (Research Agent) collecting compliance rules...")
        tracker.record_event(
            prompt_tokens=120,
            completion_tokens=250,
            completion_string="Gathered regulatory guidelines for transfer.",
            agent_state={"agent_role": "researcher", "step": 1}
        )

        # Agent B: Execution Agent
        print("  - Agent B (Execution Agent) performing action...")
        tracker.record_event(
            prompt_tokens=80,
            completion_tokens=150,
            completion_string="Prepared wire transfer payload.",
            tool_calls=[{"name": "prepare_transfer", "arguments": {"amount": 2500}}],
            agent_state={"agent_role": "executor", "step": 2}
        )

    tracker.flush()
    tracker.shutdown()

    # Call Gateway with State Hash Caching
    client = httpx.Client(timeout=5.0)
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "Execute compliance transfer of $2500"}]
    }
    headers = {
        "X-AgentTrace-Correlation-ID": correlation_id,
        "X-AgentTrace-Enable-Caching": "true",
        "X-AgentTrace-State-Hash": "state_hash_multi_agent_v1"
    }

    try:
        print("\n[2] Executing LLM request via Gateway Proxy...")
        res = client.post(f"{gateway_url}/v1/chat/completions", json=payload, headers=headers)
        if res.status_code == 200:
            print(f"      Gateway Response Status: 200 OK | Cache Hit: {res.headers.get('X-AgentTrace-Cache-Hit')}")
    except Exception as e:
        print(f"      Gateway proxy note: {e}")

    time.sleep(1.0)

    # Seal WORM session
    try:
        print("\n[3] Sealing WORM Session & Requesting Ed25519 Proof Receipt...")
        seal_res = client.post(f"{ingest_url}/ingest/seal", json={"correlation_id": correlation_id})
        if seal_res.status_code == 200:
            seal_data = seal_res.json()
            print(f"      WORM Session Sealed. Signature: {seal_data.get('hmac_signature', '')[:32]}...")
    except Exception as e:
        print(f"      Ingestion service note: {e}")

    client.close()


if __name__ == "__main__":
    run_multi_agent_workflow()
