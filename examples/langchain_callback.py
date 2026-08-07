"""Tiny LangChain-style callback example for local telemetry correlation."""

from llmwitness.sdk import trace_session


def run_chain():
    with trace_session("langchain-chain") as correlation_id:
        print(f"Attach correlation ID {correlation_id} to your chain run")
