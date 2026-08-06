"""
Legacy compatibility layer for config.
Forwards configuration validator to agenttrace.config.
"""

from agenttrace.config import AgentTraceConfig, get_config

__all__ = ["AgentTraceConfig", "get_config"]
