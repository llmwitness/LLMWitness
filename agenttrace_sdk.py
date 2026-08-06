"""
Legacy compatibility layer for agenttrace_sdk.
Forwards all imports to agenttrace.sdk package.
"""

from agenttrace.sdk import (
    AgentTraceTracker,
    _current_correlation_id,
    _current_task_name,
    get_current_correlation_id,
)

__all__ = [
    "AgentTraceTracker",
    "get_current_correlation_id",
    "_current_correlation_id",
    "_current_task_name",
]
