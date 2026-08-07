"""Autogen/CrewAI-style example for recording agent runs."""

from llmwitness import LLMWitnessTracker


def record_agent_run():
    tracker = LLMWitnessTracker(ingestion_url="http://127.0.0.1:8000")
    with tracker.trace_session("multi_agent_run") as correlation_id:
        tracker.record_event(
            correlation_id=correlation_id,
            task_name="planner",
            completion_string="Planner delegated tasks successfully.",
        )
    tracker.flush()
    tracker.shutdown()
