"""
LLMWitness Quickstart Example
Demonstrates local SDK telemetry and a development gateway request.
"""

import httpx

from llmwitness import LLMWitnessTracker, generate_uuidv7


def main():
    print("--- LLMWitness Quickstart Example ---")

    # 1. Initialize Telemetry Tracker
    tracker = LLMWitnessTracker(ingestion_url="http://localhost:8000")
    correlation_id = generate_uuidv7()

    # 2. Record Agent Telemetry Session
    with tracker.trace_session(
        task_name="quickstart_agent_task", correlation_id=correlation_id
    ):
        print(f"Session Correlation ID (UUIDv7): {correlation_id}")

        tracker.record_event(
            prompt_tokens=25,
            completion_tokens=45,
            completion_string="Agent quickstart task executed successfully.",
            tool_calls=[{"name": "lookup_user", "arguments": {"user_id": 42}}],
            agent_state={"step": 1, "status": "ok"},
        )

    tracker.flush()
    tracker.shutdown()
    print("Telemetry recorded and queued asynchronously.")

    # 3. Invoke the gateway. Scrubbing applies to the audit copy, not this response.
    client = httpx.Client(timeout=5.0)
    gateway_url = "http://localhost:8011/v1/chat/completions"

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": "Customer request containing SSN 123-45-6789 and token EXAMPLE_TOKEN_VALUE",
            }
        ],
    }
    headers = {"X-LLMWitness-Correlation-ID": correlation_id}

    try:
        response = client.post(gateway_url, json=payload, headers=headers)
        if response.status_code == 200:
            print("Gateway Proxy Response:")
            print(response.json())
        else:
            print(f"Gateway returned status: {response.status_code}")
    except Exception as e:
        print(
            f"Gateway connection note: ensure llmwitness.gateway is running on port 8011 ({e})."
        )

    client.close()


if __name__ == "__main__":
    main()
