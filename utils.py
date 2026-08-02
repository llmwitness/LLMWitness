import hashlib
import hmac
import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Union


def generate_uuidv7() -> str:
    """
    Generate an RFC 9562 compliant UUIDv7 identifier.
    Uses 48-bit millisecond timestamp + 4-bit version 7 + 12-bit rand_a + 2-bit variant + 62-bit rand_b.
    """
    ms_timestamp = int(time.time() * 1000)
    rand_a = int.from_bytes(os.urandom(2), byteorder="big") & 0x0FFF
    high = (ms_timestamp << 16) | (0x7 << 12) | rand_a
    rand_b = int.from_bytes(os.urandom(8), byteorder="big") & 0x3FFFFFFFFFFFFFFF
    low = (0x2 << 62) | rand_b
    val = (high << 64) | low
    return str(uuid.UUID(int=val))


# Regex patterns for sensitive PII data
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
API_TOKEN_REGEX = re.compile(
    r"(?i)\b(sk-[a-zA-Z0-9_-]{20,}|bearer\s+[a-zA-Z0-9._\-]{20,}|api[_-]?key[\s:=]+['\"]?[a-zA-Z0-9._\-]{16,}['\"]?)"
)


def get_default_allow_list() -> List[str]:
    """Retrieve global PII allow-list items from environment setting."""
    env_allow = os.getenv("AGENTTRACE_PII_ALLOW_LIST", "")
    if env_allow:
        return [item.strip() for item in env_allow.split(",") if item.strip()]
    return []


def redact_pii(
    content: Union[str, Dict[str, Any]], allow_list: Optional[List[str]] = None
) -> Union[str, Dict[str, Any]]:
    """
    Scrub PII (Social Security Numbers, Credit Cards, API Tokens) from string or JSON structure.
    Protects benign tracking codes or user-defined allowed terms passed in allow_list.
    """
    effective_allow = (allow_list or []) + get_default_allow_list()

    if isinstance(content, dict):
        cleaned_dict = {}
        for key, val in content.items():
            if isinstance(val, (str, dict, list)):
                cleaned_dict[key] = redact_pii(val, allow_list=effective_allow)
            else:
                cleaned_dict[key] = val
        return cleaned_dict
    elif isinstance(content, list):
        return [redact_pii(item, allow_list=effective_allow) for item in content]
    elif isinstance(content, str):
        # Preserve items present in allow-list by temporary token substitution
        placeholders = {}
        processed_text = content
        for idx, allowed_term in enumerate(effective_allow):
            if allowed_term in processed_text:
                ph_token = f"__AGENTTRACE_ALLOW_PH_{idx}__"
                placeholders[ph_token] = allowed_term
                processed_text = processed_text.replace(allowed_term, ph_token)

        text = SSN_REGEX.sub("[REDACTED_SSN]", processed_text)
        text = CREDIT_CARD_REGEX.sub("[REDACTED_CREDIT_CARD]", text)
        text = API_TOKEN_REGEX.sub("[REDACTED_API_TOKEN]", text)

        # Restore preserved allow-list items
        for ph_token, orig_val in placeholders.items():
            text = text.replace(ph_token, orig_val)

        return text
    return content


def compute_hmac_signature(payload: Union[str, bytes], secret_key: Union[str, bytes]) -> str:
    if isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    else:
        payload_bytes = payload

    if isinstance(secret_key, str):
        key_bytes = secret_key.encode("utf-8")
    else:
        key_bytes = secret_key

    return hmac.new(key_bytes, payload_bytes, hashlib.sha256).hexdigest()


def verify_hmac_signature(payload: Union[str, bytes], signature: str, secret_key: Union[str, bytes]) -> bool:
    expected_sig = compute_hmac_signature(payload, secret_key)
    return hmac.compare_digest(expected_sig, signature)
