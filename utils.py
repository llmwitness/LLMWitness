"""
Legacy compatibility layer for utils.
Forwards cryptographic proof helpers and PII engine to agenttrace.utils.
"""

from agenttrace.utils import (
    API_TOKEN_REGEX,
    CREDIT_CARD_REGEX,
    DATA_IMAGE_REGEX,
    SSN_REGEX,
    Ed25519KeyManager,
    _is_raw_base64_image,
    compute_hmac_signature,
    generate_uuidv7,
    get_default_allow_list,
    redact_payload,
    redact_pii,
    verify_proof_receipt,
)

__all__ = [
    "generate_uuidv7",
    "redact_payload",
    "redact_pii",
    "get_default_allow_list",
    "_is_raw_base64_image",
    "Ed25519KeyManager",
    "compute_hmac_signature",
    "verify_proof_receipt",
    "SSN_REGEX",
    "CREDIT_CARD_REGEX",
    "API_TOKEN_REGEX",
    "DATA_IMAGE_REGEX",
]
