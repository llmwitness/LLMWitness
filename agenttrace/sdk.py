import contextvars
import json
import queue
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union
import httpx

from agenttrace.utils import generate_uuidv7, redact_pii

# Thread-local / Context-local correlation ID tracker
_current_correlation_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "agenttrace_correlation_id", default=None
)
_current_task_name: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "agenttrace_task_name", default=None
)


def get_current_correlation_id() -> Optional[str]:
    """Retrieve active X-AgentTrace-Correlation-ID from current execution context."""
    return _current_correlation_id.get()


class AgentTraceTracker:
    """
    Python SDK telemetry client for AgentTrace.
    Captures model interactions, tool calls, and state variables using non-blocking background queue streaming.
    """

    def __init__(self, ingestion_url: str = "http://localhost:8000"):
        self.ingestion_url = ingestion_url.rstrip("/")
        self.queue: queue.Queue = queue.Queue()
        self.running = True
        self.http_client = httpx.Client(timeout=10.0)

        # Start background worker thread for non-blocking telemetry streaming
        self.worker_thread = threading.Thread(
            target=self._telemetry_worker, daemon=True, name="AgentTraceTelemetryWorker"
        )
        self.worker_thread.start()

    def _telemetry_worker(self):
        """Worker loop reading telemetry items from queue and dispatching to Ingestion Engine."""
        while self.running or not self.queue.empty():
            try:
                payload = self.queue.get(timeout=0.2)
                try:
                    self.http_client.post(
                        f"{self.ingestion_url}/ingest/sdk",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                except Exception as err:
                    print(f"[AgentTrace SDK Warning] Failed to stream telemetry: {err}")
                finally:
                    self.queue.task_done()
            except queue.Empty:
                continue

    def record_event(
        self,
        task_name: Optional[str] = None,
        correlation_id: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        completion_string: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        agent_state: Optional[Dict[str, Any]] = None,
    ):
        """
        Pushes a telemetry payload into the background queue without blocking caller execution.
        """
        active_cid = correlation_id or _current_correlation_id.get() or generate_uuidv7()
        active_task = task_name or _current_task_name.get() or "default_task"

        payload = {
            "correlation_id": active_cid,
            "task_name": active_task,
            "timestamp": time.time(),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "completion_string": redact_pii(completion_string) if completion_string else None,
            "tool_calls": redact_pii(tool_calls) if tool_calls else [],
            "agent_state": redact_pii(agent_state) if agent_state else {},
        }
        self.queue.put(payload)

    @contextmanager
    def trace_session(self, task_name: str, correlation_id: Optional[str] = None):
        """
        Automated context manager generating or binding a unique UUIDv7 correlation ID.
        """
        cid = correlation_id or generate_uuidv7()
        token_cid = _current_correlation_id.set(cid)
        token_task = _current_task_name.set(task_name)
        try:
            yield cid
        finally:
            _current_correlation_id.reset(token_cid)
            _current_task_name.reset(token_task)

    def wrap_openai_client(self, client: Any) -> Any:
        """
        Wraps an OpenAI client instance to automatically record prompt tokens, completion strings,
        and function/tool calls with the current session correlation ID.
        """
        tracker = self

        original_create = client.chat.completions.create

        def intercepted_create(*args, **kwargs):
            cid = get_current_correlation_id() or generate_uuidv7()
            if "extra_headers" in kwargs:
                kwargs["extra_headers"]["X-AgentTrace-Correlation-ID"] = cid
            else:
                kwargs["extra_headers"] = {"X-AgentTrace-Correlation-ID": cid}

            response = original_create(*args, **kwargs)

            try:
                usage = getattr(response, "usage", None)
                p_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
                c_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

                choices = getattr(response, "choices", [])
                completion_str = ""
                tool_calls_data = []

                if choices:
                    msg = getattr(choices[0], "message", None)
                    if msg:
                        completion_str = getattr(msg, "content", "") or ""
                        raw_tool_calls = getattr(msg, "tool_calls", None)
                        if raw_tool_calls:
                            for tc in raw_tool_calls:
                                tool_calls_data.append({
                                    "id": getattr(tc, "id", ""),
                                    "type": getattr(tc, "type", "function"),
                                    "function": {
                                        "name": getattr(getattr(tc, "function", None), "name", ""),
                                        "arguments": getattr(getattr(tc, "function", None), "arguments", "")
                                    }
                                })

                tracker.record_event(
                    correlation_id=cid,
                    prompt_tokens=p_tokens,
                    completion_tokens=c_tokens,
                    completion_string=completion_str,
                    tool_calls=tool_calls_data
                )
            except Exception as ex:
                print(f"[AgentTrace SDK Warning] Failed to parse OpenAI completion metadata: {ex}")

            return response

        client.chat.completions.create = intercepted_create
        return client

    def flush(self):
        """Block until all queued telemetry items are dispatched."""
        self.queue.join()

    def shutdown(self):
        """Shutdown background worker thread cleanly."""
        self.running = False
        self.http_client.close()
