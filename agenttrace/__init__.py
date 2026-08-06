"""
AgentTrace - Immutable Audit Logging & Edge PII Masking Gateway for Autonomous AI Agents.
"""

__version__ = "0.1.0"
__author__ = "AgentTrace Core Engineering Committee"

from agenttrace.sdk import AgentTraceTracker, get_current_correlation_id
from agenttrace.utils import (
    Ed25519KeyManager,
    compute_hmac_signature,
    generate_uuidv7,
    redact_payload,
    redact_pii,
    verify_proof_receipt,
)

__all__ = [
    "__version__",
    "AgentTraceTracker",
    "get_current_correlation_id",
    "redact_pii",
    "redact_payload",
    "generate_uuidv7",
    "verify_proof_receipt",
    "Ed25519KeyManager",
    "compute_hmac_signature",
]
