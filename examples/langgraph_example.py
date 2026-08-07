"""Minimal LangGraph-style example for LLMWitness."""

from llmwitness.sdk import trace_session


def run_graph():
    with trace_session("langgraph-flow") as correlation_id:
        print(f"Attach correlation ID {correlation_id} to your graph state")
