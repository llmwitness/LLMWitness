import threading
import uuid

import pytest

from llmwitness import LLMWitnessTracker, get_current_correlation_id, trace_session


class _Response:
    def raise_for_status(self):
        return None


def test_session_correlation_is_uuidv7_and_propagates(monkeypatch):
    delivered = []
    delivered_event = threading.Event()
    tracker = LLMWitnessTracker(ingestion_url="http://ingest.invalid")

    def post(*args, **kwargs):
        delivered.append(kwargs["json"])
        delivered_event.set()
        return _Response()

    monkeypatch.setattr(tracker.http_client, "post", post)
    with tracker.trace_session("root-task") as correlation_id:
        parsed = uuid.UUID(correlation_id)
        assert parsed.version == 7
        assert get_current_correlation_id() == correlation_id
        assert tracker.record_event(prompt_tokens=3) == correlation_id

    assert delivered_event.wait(1)
    tracker.shutdown()
    assert delivered[0]["correlation_id"] == correlation_id
    assert delivered[0]["task_name"] == "root-task"
    assert get_current_correlation_id() is None


def test_module_session_and_shutdown_drain_queue(monkeypatch):
    delivered = []
    tracker = LLMWitnessTracker(ingestion_url="http://ingest.invalid")
    monkeypatch.setattr(
        tracker.http_client,
        "post",
        lambda *args, **kwargs: delivered.append(kwargs["json"]) or _Response(),
    )

    with trace_session("shared", "019fd93b-a06b-7799-947f-67f80b9edc04") as cid:
        tracker.record_event()
        assert cid == "019fd93b-a06b-7799-947f-67f80b9edc04"

    tracker.shutdown()
    tracker.shutdown()  # idempotent
    assert [item["correlation_id"] for item in delivered] == [cid]
    with pytest.raises(RuntimeError, match="shut down"):
        tracker.record_event()
