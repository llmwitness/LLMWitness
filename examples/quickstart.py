"""
AgentTrace Quickstart Example
Demonstrates basic Python SDK telemetry recording and Gateway proxy invocation with inline PII redaction.
"""

import os
import sys
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agenttrace_sdk import AgentTraceTracker
from utils import generate_uuidv7


def main():
    print("--- AgentTrace Quickstart Example ---")

    # 1. Initialize Telemetry Tracker
    tracker = AgentTraceTracker(ingestion_url="http://localhost:8000")
    correlation_id = generate_uuidv7()

    # 2. Record Agent Telemetry Session
    with tracker.trace_session(task_name="quickstart_agent_task", correlation_id=correlation_id):
        print(f"Session Correlation ID (UUIDv7): {correlation_id}")

        tracker.record_event(
            prompt_tokens=25,
            completion_tokens=45,
            completion_string="Agent quickstart task executed successfully.",
            tool_calls=[{"name": "lookup_user", "arguments": {"user_id": 42}}],
            agent_state={"step": 1, "status": "ok"}
        )

    tracker.flush()
    tracker.shutdown()
    print("Telemetry recorded and queued asynchronously.")

    # 3. Invoke Gateway Proxy with PII Redaction
    client = httpx.Client(timeout=5.0)
    gateway_url = "http://localhost:8011/v1/chat/completions"

    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": "Customer request containing SSN 123-45-6789 and token sk-12345678901234567890abcdef"}
        ]
    }
    headers = {
        "X-AgentTrace-Correlation-ID": correlation_id,
        "X-AgentTrace-Enable-Caching": "true"
    }

    try:
        response = client.post(gateway_url, json=payload, headers=headers)
        if response.status_code == 200:
            print("Gateway Proxy Response:")
            print(response.json())
        else:
            print(f"Gateway returned status: {response.status_code}")
    except Exception as e:
        print(f"Gateway connection note: Ensure gateway.py is running on port 8011 ({e}).")

    client.close()


if __name__ == "__main__":
    main()
