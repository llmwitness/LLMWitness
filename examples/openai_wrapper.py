"""Minimal OpenAI wrapper example for LLMWitness."""

from llmwitness.sdk import LLMWitnessTracker


def build_client(client):
    tracker = LLMWitnessTracker(ingestion_url="http://127.0.0.1:8000")
    return tracker.wrap_openai_client(client)

